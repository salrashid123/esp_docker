#!/usr/bin/python

from __future__ import print_function

import time, os
from random import randint
import grpc
import task_pb2_grpc
import task_pb2

from google.protobuf.empty_pb2 import Empty

import google.auth
from google.auth import exceptions
from google.auth import transport
from google.oauth2 import id_token
import google_auth_httplib2

import google.auth.transport.requests
import requests

_TIMEOUT_SECONDS = 10

def run():
  
  # for nonSSL to ESP port http2: 8081
  #channel = grpc.insecure_channel('main.esodemoapp2.com:8081')

  # for nonSSL direct to GRPC server port 50051
  channel = grpc.insecure_channel('main.esodemoapp2.com:50051')

  # for SSL to ESP (port: 8082)
  #ssl_credentials = grpc.ssl_channel_credentials(open('../certs/ssl_certs/CA_crt.pem').read())
  #channel = grpc.secure_channel('main.esodemoapp2.com:8082', ssl_credentials)
  
  stub = task_pb2_grpc.ToDoServiceStub(channel)
  
  metadata = []

  credentials, project = google.auth.default()
  g_request = google.auth.transport.requests.Request()
  credentials.refresh(g_request)
  auth_token = credentials.id_token
  print(auth_token)

  api_key = None

  if api_key:
      metadata.append(('x-api-key', api_key))
  if auth_token:
      metadata.append(('authorization', 'Bearer ' + auth_token))

  print("---- LIST ---- ")
  list_response = stub.ListToDo(Empty(), metadata=metadata)
  for f in list_response.result:
    print(f)

  print("---- CREATE ---- ")
  id = (randint(0, 10000))
  t = task_pb2.ToDo(id=id, task='some task')
  r = stub.CreateToDo(task_pb2.CreateToDoRequest(id=id,message=t),_TIMEOUT_SECONDS,metadata=metadata)
  print(r)
  

  print("---- LIST ---- ")
  list_response = stub.ListToDo(Empty(),metadata=metadata)
  for f in list_response.result:
    print(f)

  print("---- GET  ---- ")
  r = stub.GetToDo(task_pb2.GetToDoRequest(id=id),_TIMEOUT_SECONDS, metadata=metadata)
  print(r)

  print("---- DELETE ---- ")
  r = stub.DeleteToDo(task_pb2.DeleteToDoRequest(id=id),_TIMEOUT_SECONDS, metadata=metadata)
  print(r)

  print("---- LIST ---- ")
  list_response = stub.ListToDo(Empty(), metadata=metadata)
  for f in list_response.result:
    print(f)

if __name__ == '__main__':
  run()
