import urllib, urllib2
import json
from icalendar import Calendar
# https://github.com/collective/icalendar
from flask import Flask, request, redirect, url_for

app = Flask(__name__)

# set the callback urls
# and get the client_ids and client_secrets at
# https://developer.wunderlist.com/applications
# https://accounts.coursera.org/console/
#
# doc for WL API
# https://developer.wunderlist.com/documentation
#
# doc for Coursera API
# https://tech.coursera.org/app-platform/

services = ['wunderlist', 'coursera']

oauth = {}

for service in services:
    # add 'mysite/' before service below if deploying on Pythonanywhere
    with open(service + '_oauth.json') as data_file:
        oauth[service] = json.load(data_file)

def fetch_from_api(service, fetch_url):
    uri = fetch_url % (oauth[service]['token'], oauth[service]['client_id'])
    resp = urllib2.urlopen(uri).read()
    r = json.loads(resp)
    return r

def push_to_api(service, push_url, payload):
    headers = { 'X-Access-Token' : oauth[service]['token'], 'X-Client-ID' : oauth[service]['client_id'], 'Content-Type' : 'application/json' }
    req = urllib2.Request(push_url, json.dumps(payload), headers)
    return urllib2.urlopen(req).read()

def redirects(page):
    if page in services:
      uri = oauth[page]['authentication_url'] % (oauth[page]['client_id'], oauth[page]['callback_url'])
    else:
      uri = url_for(page)
    return uri

@app.route('/')
def root():
    return redirect(redirects('coursera'))

@app.route('/callback/<service>', methods=["GET"])
def callback(service):
    code = request.args.get('code')
    s = oauth[service]
    uri = s['token_url']
    params = urllib.urlencode({'client_id': s['client_id'], 'client_secret': s['client_secret'], 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': s['callback_url']})
    resp = urllib2.urlopen(uri, params)
    r = json.loads(resp.read())
    oauth[service]['token'] = r['access_token']
    return redirect(redirects(s['redirect']))

@app.route('/logic')
def logic():
    # keying together active sessionIds and names on courseId
    resp = fetch_from_api('coursera', 'https://api.coursera.org/api/users/v1/me/enrollments?access_token=%s&client_id=%s')
    actives = {}
    for enrollment in resp['enrollments']:
      if enrollment['startStatus'] == 'Present':
        actives[enrollment['courseId']] = {'sessionId' : enrollment['sessionId']}
    for course in resp['courses']:
      if course['id'] in actives:
        actives[course['id']]['name'] = course['name']

    # keying together name and newly created Wunderlist list id on sessionId
    courses = {}
    for key, value in actives.iteritems():
      courses[value['sessionId']] = {'name' : value['name']}
      resp = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/lists', { "title" : value['name'] })
      courses[value['sessionId']]['list_id'] = json.loads(resp)['id']

    # get all calendars and push their items to the respective lists
    resp = urllib2.urlopen('https://api.coursera.org/api/catalog.v1/sessions')
    r = json.loads(resp.read())
    for session in r['elements']:
      if session['id'] in courses.keys():
        resp = urllib2.urlopen('http://class.coursera.org/%s/api/course/calendar' % (session['homeLink'].split('/')[3]))
        cal = Calendar.from_ical(resp.read())
        for event in cal.walk('vevent'):
          title = event.decoded('summary')
          due_date = event.decoded('dtstart').strftime('%Y-%m-%d')
          payload = { "list_id" : courses[session['id']]['list_id'] , "title" : title, "due_date" : due_date }
          task = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/tasks', payload)
    return 'Ok.'

if __name__ == "__main__":
    app.secret_key = '53421'
    app.run(debug=True)
