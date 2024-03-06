# Data uploader client
Monitors image and scalar EPICS process variables and upload them to the image
backend and measurement database respectively.

## Building the Docker image
Pass the image backend endpoint to the docker build command:

```bash
docker build . -t image-uploader \
  --build-arg IMAGE_BACKEND_ENDPOINT_URL=http://12.34.56.78:1234/daq-image
```
