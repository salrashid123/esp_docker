package main

import (

	//"os"

	pb "echo"
	"flag"
	"log"
	"time"

	"golang.org/x/net/context"
	"google.golang.org/grpc"
	//"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/metadata"
)

const (
)

var ()

func main() {

	address := flag.String("host", "localhost:50051", "host:port of gRPC server")
	flag.Parse()

	/*
	ce, err := credentials.NewClientTLSFromFile("server_crt.pem", "")
	if err != nil {
		log.Fatalf("Failed to generate credentials %v", err)
	}
	*/
	//conn, err := grpc.Dial(*address, grpc.WithTransportCredentials(ce))
	conn, err := grpc.Dial(*address, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()

	c := pb.NewEchoServerClient(conn)

	var testMetadata = metadata.MD{
		"sal":  []string{"value1"},
		"key2": []string{"value2"},
	}

	ctx := metadata.NewOutgoingContext(context.Background(), testMetadata)

	var header, trailer metadata.MD

	for i := 0; i < 10; i++ {
		r, err := c.SayHello(ctx, &pb.EchoRequest{Name: "unary RPC msg "}, grpc.Header(&header), grpc.Trailer(&trailer))
		if err != nil {
			log.Fatalf("could not greet: %v", err)
		}
		time.Sleep(1 * time.Second)
		log.Printf("RPC Response: %v %v", i, r)
	}

}
