
import time
from datetime import timedelta, datetime
import random
import string

import base64

from google.oauth2 import id_token
from google.auth import transport
import google.auth.transport.requests

import grpc

import task_pb2_grpc
import task_pb2
from concurrent import futures
from google.protobuf.empty_pb2 import Empty
from google.protobuf.any_pb2 import Any
from google.rpc.status_pb2 import Status

from google.protobuf.any_pb2 import Any

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

ENDPOINTS_HEADER = 'X-Endpoint-API-UserInfo'
AUTHORIZATION_HEADER = 'authorization'

todo_list = {}

class ToDoService(task_pb2_grpc.ToDoServiceServicer):

  def ListToDo(self, request, context):
    meta = dict(context.invocation_metadata())
    print 'ListToDo called: '
    return task_pb2.ListToDoResponse(result=todo_list.values())

  def CreateToDo(self, request, context):
    print 'CreateToDo called: '   +  str(request.message.id)
    if (request.message.id in todo_list.keys()):
      context.set_details("ID {} already exists".format(request.message.id))
      context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
      return Empty() 
    t = task_pb2.ToDo(id=request.message.id, task=request.message.task)
    todo_list[request.message.id] = t
    return t

  def GetToDo(self, request, context):
    if not (request.id in todo_list.keys()):
      context.set_details("ID {} does not exists".format(request.id))
      context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
      return task_pb2.ToDo()
    print 'GetToDo called: '  +   str(request.id)
    return todo_list[request.id]

  def DeleteToDo(self, request, context): 
    if not (request.id in todo_list.keys()):
      context.set_details("ID {} does not exists".format(request.id))
      context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
      return Empty()
    del todo_list[request.id]
    print 'DeleteToDo called: '  +   str(request.id)
    return Empty()


def _unary_unary_rpc_terminator(code, details):
    def terminate(ignored_request, context):
        context.abort(code, details)
    return grpc.unary_unary_rpc_method_handler(terminate)

class RequestHeaderValidatorInterceptor(grpc.ServerInterceptor):

    def __init__(self):
        self._terminator = _unary_unary_rpc_terminator(grpc.StatusCode.UNAUTHENTICATED, 'Access Denied')

    def intercept_service(self, continuation, handler_call_details):
      try:
        for k in handler_call_details.invocation_metadata:
          if ( k.key.lower() ==  AUTHORIZATION_HEADER ):
            token = k.value
            token = token.split(' ')[1]
            r = google.auth.transport.requests.Request()
            id_token.verify_token(token,r)
            return continuation(handler_call_details)
        return self._terminator
      except:
        return self._terminator        

def serve():

  header_validator = RequestHeaderValidatorInterceptor()

  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=(header_validator,))
  task_pb2_grpc.add_ToDoServiceServicer_to_server(ToDoService(),server)

  server.add_insecure_port('[::]:50051')
  print("starting server [::]:50051")
  server.start()
  try:
    while True:
      time.sleep(_ONE_DAY_IN_SECONDS)
  except KeyboardInterrupt:
    server.stop()

if __name__ == '__main__':
  serve()
