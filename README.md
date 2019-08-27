
# Google Cloud Endpoints: REST and gRPC, gRPC+Transcoding

## Introduction

A month or so ago, a customer of mine wanted to use [Cloud Endpoints](https://cloud.google.com/endpoints/docs/) but wanted to run the ESP (Extensible Server Proxy) stand-alone on their server.  Normally, Cloud Endpoints is run on GKE, GAE Flex or via the [Endpoints Framework](https://cloud.google.com/endpoints/docs/frameworks/about-cloud-endpoints-frameworks) on GAE Standard.  However,
the proxy can easily run [on another platform](https://cloud.google.com/endpoints/docs/openapi/running-esp-localdev).  

This repo demonstrates an end-to-end sample of running ESP on Docker but also proceeds to show:

- Running REST Backend service.
- Running gRPC Backend Service
- Running gRPC with HTTP Transcoding
- Using gcloud Application Default Credentials to authenticate.

The article first deploys a backend implemented as pure REST and its corresponding client.  Then a gRPC Server which includes provisions for HTTP Transcoding.
This sample will allow you to call the backend via HTTP or gRPC on separate ports or with SSL, on the same port.  Both samples demonstrates how to acquire a Bearer token for google authentication.

Finally, the HTTP and gRPC backends are protected by Google Authentication which means each call must have a google-issued ID token in the HEADER.
The ESP proxy validates the header value and just as a precaution, i've added in a secondary check in Flask Middleware as well as gRPC Interceptor.

I've added some links to the Appendix for each of these for reference.

- [ESP and gRPC](https://cloud.google.com/endpoints/docs/grpc/about-grpc)
- [Proxy Startup Options](https://cloud.google.com/endpoints/docs/openapi/specify-proxy-startup-options)
- [Google Authenticaiton](https://cloud.google.com/endpoints/docs/frameworks/authentication-method#google_authentication)
- [Endpoints on GCE](https://cloud.google.com/endpoints/docs/grpc/get-started-grpc-compute-engine-docker)

To be clear, i'm not doing anything in this repo that is not already documented in various places.  I find it easier to understand things from scratch
and developing my own samples along the way focusing on aspects i'm interested in.


Lets get started.


### Clone the Repo

```
git clone https://github.com/salrashid123/esp_docker.git
```

### Create a GCP cloud project

 If you already have one handy, thats fine.  In the examples below, my project is: ```espdemo-199923```


### Create a Service Account Key and download it.

On the GCP Cloud console, goto
- "IAM & Admin" >> "Service Accounts" >> "Create Service Account".  You can call the service account anyting (I called it ```espsvc```).  
- Select "Furnish new Public Key" and select JSON.
- Assign the "Service Management >> Service Controller" role to this account.
- Click download to crate the key and copy the json file to the ```esp_docker/certs/esp_certs``` folder from the repo root.

### REST

The following sections details how to stand up a HTTP-only endpoint and ESP

#### Deploy ESP Config

- ```cd esp_docker/http```
- Edit ```http/openapi.yaml```
    - Replace ```YOUR_PROJECT``` with your projectID
    - in my case, the value is: ```host: api.endpoints.espdemo-199923.cloud.goog```


then

```
gcloud endpoints services deploy openapi.yaml
```


You can verify the configurations active by running the following or by viewing the ```Endpoints``` section of the Cloud Console

```
$ gcloud endpoints configs list --service=api.endpoints.espdemo-199923.cloud.goog
CONFIG_ID     SERVICE_NAME
2018-04-01r0  api.endpoints.espdemo-199923.cloud.goog
```

#### Prepare client and server environment

```
virtualenv env
source env/bin/activate

pip install -r requirements.txt
```

#### Run HTTP API server

```

$ python http_server.py
 * Running on http://0.0.0.0:50051/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 320-710-630
```

>> Note that it is listening on port ```:50051```


#### Run the ESP docker contianer

First make sure the certificzate you downloaded for the service account exits within ```esp_docker/certs/esp_certs``` foler.

Run the container as follows.  Remember to replace
- service name
- version
- servcie_account JSON filename and relative reference to the folder

Note the backend is pointing to the HTTP endpoint of your api server

```
docker run   \
    -t  \
    --net="host"  \
    --volume `pwd`/../certs/esp_certs:/esp  \
    gcr.io/endpoints-release/endpoints-runtime:1  \
    --service  api.endpoints.espdemo-199923.cloud.goog  \
    --version  2018-04-01r0   \
    --http_port  8080  \
    --backend 127.0.0.1:50051  \
    --service_account_key /esp/espdemo-abfabcd372f8.json
```

#### Run HTTP_Client

In a new window, navigate to the ```esp_docker/http``` folder and initialize the virtualenv:
```
cd esp_docker/http
source env/bin/activate
```

then run the client:

```
$ python http_client.py

++++++++++++++ mint and verify id_token for current user ++++++++++++++++
id_token: <REDACTED>
-------------- list
{
    "items": []
}

-------------- put
{
    "id": 111,
    "task": "some task"
}

-------------- list
{
    "items": [
        {
            "id": 111,
            "task": "some task"
        }
    ]
}

-------------- get
{
    "id": 111,
    "task": "some task"
}

-------------- delete

-------------- list
{
    "items": []
}
```

On your API server, you should see

API Server:
```
127.0.0.1 - - [01/Apr/2018 16:55:54] "GET /todos HTTP/1.1" 200 -
127.0.0.1 - - [01/Apr/2018 16:55:54] "POST /todos HTTP/1.1" 201 -
127.0.0.1 - - [01/Apr/2018 16:55:54] "GET /todos HTTP/1.1" 200 -
127.0.0.1 - - [01/Apr/2018 16:55:55] "GET /todos/111 HTTP/1.1" 200 -
127.0.0.1 - - [01/Apr/2018 16:55:55] "DELETE /todos/111 HTTP/1.1" 204 -
127.0.0.1 - - [01/Apr/2018 16:55:55] "GET /todos HTTP/1.1" 200 -
```

On the ESP Proxy, you should see:
```
127.0.0.1 - - [01/Apr/2018:23:55:54 +0000] "GET /todos HTTP/1.1" 200 20 "-" "python-requests/2.18.4"
127.0.0.1 - - [01/Apr/2018:23:55:54 +0000] "POST /todos HTTP/1.1" 201 44 "-" "python-requests/2.18.4"
127.0.0.1 - - [01/Apr/2018:23:55:54 +0000] "GET /todos HTTP/1.1" 200 101 "-" "python-requests/2.18.4"
127.0.0.1 - - [01/Apr/2018:23:55:55 +0000] "GET /todos/111 HTTP/1.1" 200 44 "-" "python-requests/2.18.4"
127.0.0.1 - - [01/Apr/2018:23:55:55 +0000] "DELETE /todos/111 HTTP/1.1" 204 0 "-" "python-requests/2.18.4"
127.0.0.1 - - [01/Apr/2018:23:55:55 +0000] "GET /todos HTTP/1.1" 200 20 "-" "python-requests/2.18.4"
```

Note, the ```id_token``` is just a JWT that you can decode at [jwt.io](jwt.io) and use that directly in a curl request to ESP:

```
{
  "alg": "RS256",
  "kid": "e9b56cfc640d12bff4540553402c7f157d481806"
}
.
{
  "azp": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
  "aud": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
  "sub": "108157913093274845221",
  "email": "your_gcloud_user@gmail.com",
  "email_verified": true,
  "at_hash": "YJQZVDRk6ewzGcNVYVdddd",
  "exp": 1522630554,
  "iss": "accounts.google.com",
  "iat": 1522626954
}
```

> *NOTE:* The example here used [Application Default Credentials](https://cloud.google.com/docs/authentication/production#providing_credentials_to_your_application) as
provided by the embedded client_id for gcloud SDK: ```764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com```.  Use of that specific client_id is not
recommended for production use as Google can change the clientID for the ```gcloud``` without notice.  The sample was provied just for convenience.

#### Cleanup
Stop the API server and docker container for ESP (you may need to run ```docker ps``` and then ```docker stop <container_id_of_esp>```)

---

### gRPC

#### Setup gRPC environment

Prepare the python environemtn to deploy gRPC server and ESP:

```bash
cd esp_docker/grpc

virtualenv env
source env/bin/activate
pip install google-cloud grpcio-tools
export GOOGLEAPIS=/tmp/googleapis
git clone https://github.com/googleapis/googleapis $GOOGLEAPIS

```

#### Deploy ESP Config

- Prepare ```api_descriptor.pb``` based on your .proto:

- ``` git clone https://github.com/googleapis/googleapis.git ```


```bash
python -m grpc_tools.protoc \
    --include_imports \
    --include_source_info \
    --proto_path=.:$GOOGLEAPIS \
    --descriptor_set_out=api_descriptor.pb \
    --python_out=. \
    --grpc_python_out=. \
    task.proto
```

(you should see ```api_descriptor.pb``` and the ```task_pb2*```)

- Edit ```esp_docker/grpc/api_config.yaml``` and set the projectID.
    -  In my case its: ```name: api.endpoints.espdemo-199923.cloud.goog```


Then

```
gcloud endpoints services deploy api_descriptor.pb api_config.yaml
```

You should see two configurations  if you deployed the HTTP sample above
```
$ gcloud endpoints configs list --service=api.endpoints.espdemo-199923.cloud.goog
CONFIG_ID     SERVICE_NAME
2018-04-02r0  api.endpoints.espdemo-199923.cloud.goog   << gRPC
2018-04-01r0  api.endpoints.espdemo-199923.cloud.goog   << HTTP
```

#### Prepare client and server environment

In a new window, Run gRPC server

```bash
cd esp_docker/grpc/
source env/bin/activate

python grpc_server.py
```

the gRPC API server is listening on ```:50001```


#### Run the ESP docker container

Now run the ESP container and specify:

- service name
- version
- servcie_account JSON filename and relative reference to the folder
- set the backend to ```grpc://127.0.0.1:50001```
- http listener on ```:8080```
- http2_listener on ```:8081```

```
docker run   \
    -t  \
    --net="host"  \
    --volume `pwd`/../certs/esp_certs/:/esp  \
    gcr.io/endpoints-release/endpoints-runtime:1  \
    --service  api.endpoints.espdemo-199923.cloud.goog  \
    --version  2018-04-02r0 \
    --http_port 8080 \
    --http2_port 8081 \
    --backend grpc://127.0.0.1:50051 \
    --service_account_key /esp/espdemo-abfabcd372f8.json
```

#### Run gRPC_Client

```
cd esp_docker/grpc
source env/bin/activate

$ python grpc_client.py

---- LIST ----
---- CREATE ----
id: 2268
task: "some task"

---- LIST ----
id: 2268
task: "some task"

---- GET  ----
id: 2268
task: "some task"

---- DELETE ----

---- LIST ----
```

Gives the output:

- API Server:

```
$ python grpc_server.py
starting server [::]:50051
ListToDo called:
CreateToDo called: 2268
ListToDo called:
GetToDo called: 2268
DeleteToDo called: 2268
ListToDo called:
```

- ESP Proxy:
```
127.0.0.1 - - [02/Apr/2018:00:43:17 +0000] "POST /todo.ToDoService/ListToDo HTTP/2.0" 200 5 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
127.0.0.1 - - [02/Apr/2018:00:43:17 +0000] "POST /todo.ToDoService/CreateToDo HTTP/2.0" 200 19 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
127.0.0.1 - - [02/Apr/2018:00:43:17 +0000] "POST /todo.ToDoService/ListToDo HTTP/2.0" 200 21 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
127.0.0.1 - - [02/Apr/2018:00:43:18 +0000] "POST /todo.ToDoService/GetToDo HTTP/2.0" 200 19 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
127.0.0.1 - - [02/Apr/2018:00:43:18 +0000] "POST /todo.ToDoService/DeleteToDo HTTP/2.0" 200 5 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
127.0.0.1 - - [02/Apr/2018:00:43:18 +0000] "POST /todo.ToDoService/ListToDo HTTP/2.0" 200 5 "-" "grpc-python/1.10.0 grpc-c/6.0.0 (manylinux; chttp2; glamorous)"
```


#### Transcoding

Since we added in annotation to the ```.proto``` for HTTP transcoding, we can also run the ```esp_docker/http/http_client.py```:

In a new window:
```
cd esp_docker/http
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

then

```
$ python http_client.py
++++++++++++++ mint and verify id_token for current user ++++++++++++++++
id_token: << redactd>>
-------------- list
{}
-------------- put
{"id":"111","task":"some task"}
-------------- list
{"result":[{"id":"111","task":"some task"}]}
-------------- get
{"id":"111","task":"some task"}
-------------- delete
{}
-------------- list
{}
```


gives output:

- gRPC server:

```
ListToDo called:
ListToDo called:
CreateToDo called: 111
ListToDo called:
GetToDo called: 111
DeleteToDo called: 111
ListToDo called:
```

- ESP Proxy:
```
127.0.0.1 - - [02/Apr/2018:00:47:09 +0000] "GET /todos HTTP/1.1" 200 12 "-" "python-requests/2.18.4"
127.0.0.1 - - [02/Apr/2018:00:47:09 +0000] "POST /todos HTTP/1.1" 200 42 "-" "python-requests/2.18.4"
127.0.0.1 - - [02/Apr/2018:00:47:10 +0000] "GET /todos HTTP/1.1" 200 55 "-" "python-requests/2.18.4"
127.0.0.1 - - [02/Apr/2018:00:47:10 +0000] "GET /todos/111 HTTP/1.1" 200 42 "-" "python-requests/2.18.4"
127.0.0.1 - - [02/Apr/2018:00:47:10 +0000] "DELETE /todos/111 HTTP/1.1" 200 12 "-" "python-requests/2.18.4"
127.0.0.1 - - [02/Apr/2018:00:47:10 +0000] "GET /todos HTTP/1.1" 200 12 "-" "python-requests/2.18.4"```
```

#### gRPC and REST over same SSL port

You can also use the **SAME** port for both ```HTTP1.1``` and ```GRPC``` over SSL.  See:

- [https://cloud.google.com/endpoints/docs/grpc/transcoding#using_ssl](https://cloud.google.com/endpoints/docs/grpc/transcoding#using_ssl)

> "If SSL is enabled for communication between your clients and ESP, then clients can use the same port to make gRPC or HTTP1.1 calls. You can find out how to set up SSL for a Cloud Endpoints service in Enabling SSL."

Setting this up is a bit more complex: you need to enable ESP for SSL and set the certificate to match the ```SNI``` setting of the cert.  For this demo, i've setup a sample CA and cert to use the hostname ```main.esodemoapp2.com```

So if you're running this on your laptop, first edit ```/etc/hosts``` and set

```
127.0.0.1 main.esodemoapp2.com
```

Then lets setup the cert and compile for transcoding:

```
cd esp_docker/grpc

virtualenv env
source env/bin/activate
pip install google-cloud grpcio-tools

export GOOGLEAPIS=/tmp/googleapis
git clone https://github.com/googleapis/googleapis $GOOGLEAPIS

python -m grpc_tools.protoc \
    --include_imports \
    --include_source_info \
    --proto_path=.:$GOOGLEAPIS \
    --descriptor_set_out=api_descriptor.pb \
    --python_out=. \
    --grpc_python_out=. \
    task.proto
```

then deploy

```
gcloud endpoints services deploy api_descriptor.pb api_config.yaml
```

catpture the config version you get and the endpoint, eg:

```
Service Configuration [2018-07-04r0] uploaded for service [api.endpoints.espdemo-199923.cloud.goog]
```

Copy ```nginx.crt```, ```nginx.key``` to a folder that ESP can find via volume mount

```
cp esp_docker/certs/CA/CA_crt.pem esp_docker/certs/ssl_certs/CA_crt.pem
cp esp_docker/certs/CA/nginx.crt esp_docker/certs/ssl_certs/nginx.crt
cp esp_docker/certs/CA/nginx.key esp_docker/certs/ssl_certs/nginx.key
```
(note, you can generate your own certs as shown below)

then run ESP (note the volume mounts)
```
cd esp_docker

docker run   \
    -t  \
    --net="host"  \
    --volume `pwd`/certs/ssl_certs/:/etc/nginx/ssl/ \
    --volume `pwd`/certs/esp_certs:/esp  \
    gcr.io/endpoints-release/endpoints-runtime:1  \
    --service  api.endpoints.espdemo-199923.cloud.goog   \
    --version  2018-07-04r0  \
    --ssl_port 8082 \
    --backend grpc://127.0.0.1:50051 \
    --service_account_key /esp/espdemo-abfabcd372f8.json

```

Now run the gRPC server

```
cd esp_docker/grpc
soruce env/bin/activate
python grpc_server.py
```

#### gRPC Client

Go to ```esp_docker/grpc```, then enable SSL and set the CA Path. (eg, comment insecure_channel and uncomment secure_channel)
```
  # for nonSSL direct to GRPC server port 50051
  #channel = grpc.insecure_channel('main.esodemoapp2.com:50051')

  # for SSL to ESP (port: 8082)
  ssl_credentials = grpc.ssl_channel_credentials(open('../certs/ssl_certs/CA_crt.pem').read())
  channel = grpc.secure_channel('main.esodemoapp2.com:8082', ssl_credentials)
```

then run
```
cd esp_docker/grpc
source env/bin/activate
python grpc_client.py
```


#### HTTP Client

Go to ```esp_docker/http```, then enable SSL and set the CA Path. (eg, comment insecure_channel and uncomment secure_channel).  Remember to set
the ```verify=``` parameter on each request so you dont' see cert warning

```
# for non-SSL to ESP http: 8080
#_HOST = 'http://main.esodemoapp2.com:8080'

# for SSL to ESP
_HOST = 'https://main.esodemoapp2.com:8082'
# note: to use SSL to ESP, add in verify= for python requests pointing to CA that signed the cert:
# response = requests.get(_HOST+  '/todos', headers={'Authorization': 'Bearer ' + idt},  verify='../certs/ssl_certs/CA_crt.pem')
```

then run
```
cd esp_docker/http
source env/bin/activate
python http_client.py
```



#### CA/SSL Certs


If you want to test with your own CA, please regenerate the the CA and index,serial files:

```
cd certs/CA
rm -rf serial* index* new_certs
echo 00 > serial
touch index.txt
mkdir new_certs

openssl genrsa -out CA_key.pem 2048
openssl req -x509 -new -nodes -key CA_key.pem -days 1000 -out CA_crt.pem -config openssl.cnf -subj "/C=US/ST=California/L=Mountain View/O=Google/OU=Enterprise/CN=MyCA"

openssl genrsa -out nginx.key 2048
openssl req -config openssl.cnf -out nginx.csr -key nginx.key -new -sha256    -subj "/C=US/ST=California/L=Mountain View/O=Google/OU=Enterprise/CN=main.esodemoapp2.com"
openssl ca -config openssl.cnf -days 365 -notext  -in nginx.csr   -out nginx.crt

cp CA_crt.pem ../ssl_certs
cp nginx.* ../ssl_certs
```

note the nginx.crt should have the SNI setup:
```
$ openssl x509 -in nginx.crt -text -noout
Certificate:
        Issuer: C = US, ST = California, L = Mountain View, O = Google, OU = Enterprise, CN = MyCA
        Validity
            Not Before: Jul  1 02:00:48 2018 GMT
            Not After : Jul  1 02:00:48 2019 GMT
        Subject: C = US, ST = California, O = Google, OU = Enterprise, CN = main.esodemoapp2.com
        X509v3 extensions:
            Netscape Comment: 
                OpenSSL Generated Certificate
            X509v3 Subject Alternative Name: 
                DNS:main.esodemoapp2.com
```

### Summary

As you can see, Cloud Endpoints with ESP in docker allows you to run anywhere with a plain docker container as a proxy.
Endpoints allows for many additional features such as extended authentication, rate control and API sharing.  This specific
example focused just on the transports and minimally on the Authentication and even then, the sample used gcloud credentials just as
a demonstration.
