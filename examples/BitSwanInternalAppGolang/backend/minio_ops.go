package main

import (
	"bytes"
	"context"
	"io"
	"log"
	"net"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"gorm.io/gorm"
)

const galleryBucket = "gallery"

func mustInitMinio() *minio.Client {
	host := envOr("MINIO_HOST", "localhost")

	// Docker hostnames with "__" are invalid per HTTP RFC, causing MinIO server
	// to reject the Host header. Resolve to IP to avoid this.
	if addrs, err := net.LookupHost(host); err == nil && len(addrs) > 0 {
		host = addrs[0]
	}

	endpoint := host + ":9000"
	accessKey := envOr("MINIO_ROOT_USER", "minioadmin")
	secretKey := envOr("MINIO_ROOT_PASSWORD", "minioadmin")

	mc, err := minio.New(endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
		Secure: false,
	})
	if err != nil {
		log.Fatalf("failed to create MinIO client: %v", err)
	}
	return mc
}

func ensureBucket(mc *minio.Client) {
	ctx := context.Background()
	exists, err := mc.BucketExists(ctx, galleryBucket)
	if err != nil {
		log.Fatalf("checking bucket: %v", err)
	}
	if !exists {
		if err := mc.MakeBucket(ctx, galleryBucket, minio.MakeBucketOptions{}); err != nil {
			log.Fatalf("creating bucket: %v", err)
		}
		log.Printf("created bucket: %s", galleryBucket)
	}
}

func preseedLogo(mc *minio.Client, db *gorm.DB) {
	key := "bitswan-logo.svg"
	if galleryImageExists(db, key) {
		return
	}

	logoSVG := []byte(`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="48" height="48" viewBox="0 0 12.7 12.7" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
  <g id="layer1">
    <path d="M 1.8973129,8.434312 V 1.3690289 L 6.1506839,4.9194224 2.6286945,7.6035199 C 2.3233601,7.8307451 2.074833,8.1147768 1.8973129,8.434312 Z M 8.3377281,6.737224 6.8252585,8.0153652 C 6.3211029,8.4556149 6.0512722,9.0449798 6.0512722,9.7195546 c 0,0.6106674 0.2414286,1.1858324 0.667476,1.6189794 0.4331482,0.433147 1.0083108,0.674575 1.6189799,0.674575 0.6106656,0 1.1858308,-0.241428 1.618979,-0.674575 0.4331489,-0.433147 0.6674729,-1.008312 0.6674729,-1.6189794 0,-0.6106678 -0.234324,-1.1858312 -0.6674729,-1.6118784 z M 10.311745,2.1359139 8.5365493,3.5205675 v 0 L 2.8275157,7.8733501 C 2.245252,8.2993973 1.8973129,8.9881737 1.8973129,9.7124541 c 0,0.6106679 0.2414259,1.1858309 0.6674731,1.6189799 0.4331485,0.433147 1.0083136,0.674574 1.6189796,0.674574 H 7.0524845 C 6.8465623,11.892396 6.6548399,11.743279 6.4773198,11.57286 5.9802652,11.075805 5.7104344,10.415432 5.7104344,9.7195546 c 0,-0.7597844 0.3124356,-1.4556617 0.8876008,-1.9598171 L 9.8643969,5.0117324 c 0.4828541,-0.4118452 0.7668841,-1.058017 0.7668841,-1.7041886 0,-0.4189465 -0.106512,-0.8165907 -0.319536,-1.1716299 z M 5.9802652,1.0139894 8.5436498,3.0945202 10.112924,1.8660839 C 10.07742,1.8234791 10.020613,1.7595721 9.9496056,1.6743626 9.4951567,1.1276019 8.8205792,1.0139894 8.3448287,1.0139894 Z"
          style="stroke-width:0.071008" />
  </g>
</svg>`)

	ctx := context.Background()
	_, err := mc.PutObject(ctx, galleryBucket, key, bytes.NewReader(logoSVG), int64(len(logoSVG)),
		minio.PutObjectOptions{ContentType: "image/svg+xml"})
	if err != nil {
		log.Printf("warning: failed to preseed logo: %v", err)
		return
	}

	if _, err := insertGalleryImage(db, key, "BitSwan Logo", "image/svg+xml", 0, "system"); err != nil {
		log.Printf("warning: failed to insert preseed record: %v", err)
	}
	log.Println("preseeded bitswan logo into gallery")
}

func uploadFile(mc *minio.Client, key string, data []byte, contentType string) error {
	ctx := context.Background()
	_, err := mc.PutObject(ctx, galleryBucket, key, bytes.NewReader(data), int64(len(data)),
		minio.PutObjectOptions{ContentType: contentType})
	return err
}

func getFile(mc *minio.Client, key string) ([]byte, string, error) {
	ctx := context.Background()
	obj, err := mc.GetObject(ctx, galleryBucket, key, minio.GetObjectOptions{})
	if err != nil {
		return nil, "", err
	}
	defer obj.Close()

	info, err := obj.Stat()
	if err != nil {
		return nil, "", err
	}

	data, err := io.ReadAll(obj)
	if err != nil {
		return nil, "", err
	}
	return data, info.ContentType, nil
}

func deleteFile(mc *minio.Client, key string) error {
	ctx := context.Background()
	return mc.RemoveObject(ctx, galleryBucket, key, minio.RemoveObjectOptions{})
}
