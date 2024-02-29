# Image analysis complete message handler
Listens to image analysis complete channel in the image backend and runs one or 
more message handlers on each incoming message.

## Handlers
### Last Analyzed Shot ID EPICS PV
The EPICS IOCs contain, for some devices, a PV (process variable) called 
`Subcomponent:Device:LastAnalyzedShotID`. This handler updates that PV. 

The user interface monitors these PVs to update plots and graphics.

## Building the Docker image
Pass the image backend Redis hostname, port, username, and password to the Docker 
build command: 

```bash
docker build . -t image-analysis-complete-handler \
  --build-arg IMAGE_BACKEND_REDIS_HOST=12.34.56.78 \
  --build-arg IMAGE_BACKEND_REDIS_PORT=6379 \
  --build-arg IMAGE_BACKEND_REDIS_USERNAME=johndoe \
  --build-arg IMAGE_BACKEND_REDIS_PASSWORD=xxxxxx
```
