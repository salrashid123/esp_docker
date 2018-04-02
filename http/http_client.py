#!/usr/bin/python

# http://google-auth.readthedocs.io/en/latest/index.html
# http://google-auth.readthedocs.io/en/latest/reference/google.auth.transport.requests.html
import os

import google.auth
from google.auth import exceptions
from google.auth import transport
from google.oauth2 import id_token
import google_auth_httplib2

import google.auth.transport.requests
import requests

# how to initialize a cred with scope and authorize a transport
scopes=['https://www.googleapis.com/auth/userinfo.email']
credentials, project = google.auth.default(scopes=scopes)
authed_http = google_auth_httplib2.AuthorizedHttp(credentials)

_HOST = 'http://localhost:8080'

print "++++++++++++++ mint and verify id_token for current user ++++++++++++++++"
# "aud": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
# "iss": "accounts.google.com",
credentials, project = google.auth.default()
g_request = google.auth.transport.requests.Request()
credentials.refresh(g_request)
idt = credentials.id_token
print 'id_token: ' + idt


print '-------------- list'
response = requests.get(_HOST+  '/todos', headers={'Authorization': 'Bearer ' + idt})
print response.text


print '-------------- put'
body = {
    'id': 111,
    'task': 'some task'
}
response = requests.post(_HOST+ '/todos', headers={'Authorization': 'Bearer ' + idt }, json = body )
print response.text


print '-------------- list'
response = requests.get(_HOST+ '/todos', headers={'Authorization': 'Bearer ' + idt})
print response.text


print '-------------- get'
response = requests.get(_HOST + '/todos/111', headers={'Authorization': 'Bearer ' + idt})
print response.text


print '-------------- delete'
response = requests.delete( _HOST+ '/todos/111', headers={'Authorization': 'Bearer ' + idt})
print response.text

print '-------------- list'
response = requests.get(_HOST+ '/todos', headers={'Authorization': 'Bearer ' + idt})
print response.text

# if you want, locally verify the id_token
#print 'id_token verification:'
#print id_token.verify_oauth2_token(idt,request)

print '--------------------------------------------------------------------------'