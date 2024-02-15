# Image uploader client
Exercitation sunt incididunt in incididunt quis incididunt pariatur. Labore nisi fugiat incididunt do duis enim. Ad sit cillum sunt culpa sit nulla aute sint laborum. Consectetur veniam veniam ullamco fugiat eu laborum. Cupidatat proident ad eu eu.

## Building the Docker image
Pass the image backend Redis hostname, port, username, and password to the Docker 
build command: 

```bash
docker build . -t image-uploader \
  --build-arg IMAGE_BACKEND_ENDPOINT_URL=http://12.34.56.78:1234/daq-image
```
