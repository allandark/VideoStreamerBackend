# VideoStreamer Backend
This repo contains a RESTFul API with an MySQL database for holding media data. The database holds metadata related to the video and the video data itself is store on a docker volume called: \"Media\". It uses the HLS (HTTP live stream) format.


## Build
#### Dependencies
- **ffmpeg**
- **Docker**

**Build docker images:**  
```
docker-compose build
```

**Run docker containers:** 
```
docker-compose build
```
