import urllib, urllib2
import json
from flask import Flask, request, redirect, url_for

app = Flask(__name__)

# set the callback url
# and get the client_id and client_secret at
# https://developer.wunderlist.com/applications
#
# doc for WL API
# https://developer.wunderlist.com/documentation

# add 'mysite/' before filename below if deploying on Pythonanywhere
with open('wunderlist_oauth.json') as data_file:
    oauth = json.load(data_file)

def fetch_from_api(fetch_url):
    uri = fetch_url % (oauth['token'], oauth['client_id'])
    resp = urllib2.urlopen(uri).read()
    r = json.loads(resp)
    return r

def push_to_api(push_url, payload, patch = False):
    headers = { 'X-Access-Token' : oauth['token'], 'X-Client-ID' : oauth['client_id'], 'Content-Type' : 'application/json' }
    req = urllib2.Request(push_url, json.dumps(payload), headers)
    if patch:
      req.get_method = lambda: 'PATCH'
    return urllib2.urlopen(req).read()

@app.route('/')
def root():
    uri = oauth['authentication_url'] % (oauth['client_id'], oauth['callback_url'])
    return redirect(uri)

@app.route('/callback/wunderlist', methods=["GET"])
def callback():
    code = request.args.get('code')
    uri = oauth['token_url']
    params = urllib.urlencode({'client_id': oauth['client_id'], 'client_secret': oauth['client_secret'], 'code': code, 'grant_type': 'authorization_code', 'redirect_uri': oauth['callback_url']})
    resp = urllib2.urlopen(uri, params)
    r = json.loads(resp.read())
    oauth['token'] = r['access_token']
    return redirect(url_for('logic'))

@app.route('/logic')
def logic():
    # get user data
    resp = fetch_from_api('https://a.wunderlist.com/api/v1/user?access_token=%s&client_id=%s')

    # make a new list called 'demo'
    resp = push_to_api('https://a.wunderlist.com/api/v1/lists', { 'title' : 'demo' })
    list_id = json.loads(resp)['id']

    # update the list title, make sure to have a proper revision property
    resp = fetch_from_api('https://a.wunderlist.com/api/v1/lists/' + str(list_id) + '?access_token=%s&client_id=%s')
    resp["title"] = 'new title'
    resp = push_to_api('https://a.wunderlist.com/api/v1/lists/' + str(resp['id']), resp, True)

    return 'Ok.'

if __name__ == "__main__":
    app.secret_key = '53421'
    app.run(debug=True)
