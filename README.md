# VideoStreamer Backend
This repository provides a RESTful API backend for managing media data with a MySQL database. It is designed to store both video metadata and the video files themselves in a Docker-managed volume named Media.

**Key features:**  
- Supports HLS (HTTP Live Streaming) for video delivery.
- All media files are stored using a SHA256 hash filename convention: SHA256_HASH.FILE_EXT.
- Provides endpoints for uploading, retrieving, and managing media metadata.
- Fully Dockerized for easy deployment alongside a React frontend.

### Upload media/video
**Steps**
1. post /api/media/upload (with media file attached)
2. post /api/video_meta/ (fillout json payload with corrosponding media_id)



## Build
#### Dependencies
- **ffmpeg**
- **Docker**


#### Build 
The SQL Container expects that a `db_root_password.txt` file, in the root dir, containing the SQL server root password.

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
