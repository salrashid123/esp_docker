# Sample application to do grpc-transcoding w/ envoy

export GOOGLEAPIS=/tmp/googleapis
git clone https://github.com/googleapis/googleapis $GOOGLEAPIS

protoc -I src/ --include_imports --include_source_info --descriptor_set_out=src/echo/echo.proto.pb -I /tmp/googleapis --go_out=plugins=grpc:src/ src/echo/echo.proto



/etc/hosts
127.0.0.1 server.domain.com

go run src/grpc_server.go --grpcport :50051



envoy
envoy -c grpc-transcoding.yaml  --log-level debug


direct
go run src/grpc_client.go --host server.domain.com:8080




$ go run src/grpc_client.go --host server.domain.com:8080
2019/05/18 14:30:37 RPC Response: 0 message:"Hello unary RPC msg   from hostname srashid3" 
2019/05/18 14:30:38 RPC Response: 1 message:"Hello unary RPC msg   from hostname srashid3" 

$ curl -v -H "Host: server.domain.com" http://localhost:8080/echo/hi

> GET /echo/hi HTTP/1.1
> Host: server.domain.com
> User-Agent: curl/7.60.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< content-type: application/json
< rpcheaderkey: val
< x-envoy-upstream-service-time: 0
< grpc-status: 0
< grpc-message: 
< content-length: 51
< date: Sat, 18 May 2019 21:30:42 GMT
< server: envoy
< 
{
 "message": "Hello hi  from hostname srashid3"
}
* Connection #0 to host localhost left intact
