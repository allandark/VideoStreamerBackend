# VideoStreamer Backend
This repo contains a RESTFul API with an MySQL database for holding media data. The database holds metadata related to the video and the video data itself is store on a docker volume called: \"Media\". It uses the HLS (HTTP live stream) format. The only media files supported for hls conversion is the `.mp4`. All media files are stored on the stored with the naming convention `SHA256_HASH.FILE_EXT`.  
### Upload media/video
**Steps**
1. post /api/media/upload (with media file attached)
2. post /api/video_meta/ (fillout json payload with corrosponding media_id)



## Build
#### Dependencies
- **ffmpeg**
- **Docker**


#### Build 
**Setup venv** 
```
python -m venv .venv
<activate_venv>
``` 

**Install requirements**

```
pip install -r requirements.txt
poetry install
```

#### Docker build
**Build docker images:**  
```
docker compose build --no-cache
```

**Run docker containers:** 
```
docker compose up -d --force-recreate
```
