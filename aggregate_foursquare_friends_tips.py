import urllib, urllib2
import json
from flask import Flask, request, redirect, url_for
import time

app = Flask(__name__)

# set the callback urls
# and get the client_ids and client_secrets at
# https://developer.wunderlist.com/applications
# https://foursquare.com/developers/apps
#
# doc for WL API
# https://developer.wunderlist.com/documentation
#
# doc for Foursquare API
# https://developer.foursquare.com/

services = ['wunderlist', 'foursquare']

oauth = {}

for service in services:
    # add 'mysite/' before service below if deploying on Pythonanywhere
    with open(service + '_oauth.json') as data_file:
        oauth[service] = json.load(data_file)

def fetch_from_api(service, fetch_url, attribute):
    uri = fetch_url % (oauth[service]['token'], attribute)
    resp = urllib2.urlopen(uri).read()
    r = json.loads(resp)
    return r

def push_to_api(service, push_url, payload, patch = False):
    headers = { 'X-Access-Token' : oauth[service]['token'], 'X-Client-ID' : oauth[service]['client_id'], 'Content-Type' : 'application/json' }
    req = urllib2.Request(push_url, json.dumps(payload), headers)
    if patch:
        req.get_method = lambda: 'PATCH'
    return urllib2.urlopen(req).read()

def redirects(page):
    if page in services:
        uri = oauth[page]['authentication_url'] % (oauth[page]['client_id'], oauth[page]['callback_url'])
    else:
        uri = url_for(page)
    return uri

@app.route('/')
def root():
    return redirect(redirects('foursquare'))

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
    # get homecity
    resp = fetch_from_api('foursquare', 'https://api.foursquare.com/v2/users/self?oauth_token=%s&v=%s', time.strftime('%Y%m%d'))
    homecity = resp['response']['user']['homeCity']

    # get all friends who have tips
    resp = fetch_from_api('foursquare', 'https://api.foursquare.com/v2/users/self/friends?oauth_token=%s&v=%s', time.strftime('%Y%m%d'))
    friends = {}
    for friend in resp['response']['friends']['items']:
        if friend['tips']['count'] != 0:
            friends[friend['id']] = friend.get('firstName', '') + ' ' + friend.get('lastName', '')

    # make a new list
    resp = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/lists', { "title" : "4SQ tips for " + homecity + " from friends." })
    list_id = json.loads(resp)['id']

    venues = {}

    # if city of tip is homecity check whether the venue is already in the list
    # if no, add venue as task and add tip as comment
    # if yes, add tip as comment and star the task
    for friend_id in friends:
        resp = fetch_from_api('foursquare', 'https://api.foursquare.com/v2/lists/' + friend_id + '/tips?oauth_token=%s&v=%s', time.strftime('%Y%m%d'))
        for tip in resp['response']['list']['listItems'].get('items', []):
            if tip['venue']['location'].get('city', '') == homecity:

                title = tip['venue']['name'] + ' (' + tip['venue']['location']['address'] + ') #' + tip['venue']['categories'][0]['name'].replace(' ', '_').lower()
                text = tip['tip']['text'] + ' (' + friends[friend_id] + ')'

                if title not in venues.keys():
                    payload = { "list_id" : list_id, "title" : title }
                    resp = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/tasks', payload)
                    task_id = json.loads(resp)['id']
                    venues[title] = task_id
                else:
                    task_id = venues[title]
                    # make sure to have a proper revision property
                    resp = fetch_from_api('wunderlist', 'https://a.wunderlist.com/api/v1/tasks/' + str(task_id) + '?access_token=%s&client_id=%s', oauth['wunderlist']['client_id'])
                    resp["starred"] = True
                    resp = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/tasks/' + str(task_id), resp, True)

                payload = { "task_id" : task_id, "text" : text }
                task_comment = push_to_api('wunderlist', 'https://a.wunderlist.com/api/v1/task_comments', payload)

    return str('Ok.')

if __name__ == "__main__":
    app.secret_key = '53421'
    app.run(debug=True)
