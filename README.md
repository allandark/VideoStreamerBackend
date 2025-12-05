# VideoStreamer Backend
A RESTful API backend for managing media data, built with Flask-RESTX, SQLAlchemy, and Alembic for database migrations. It integrates FFmpeg for video processing and uses MySQL for persistent storage. Video files are stored in a Docker-managed volume named Media. The entire service is containerized with Docker and orchestrated via Docker Compose.

## Overview
This repository provides a robust API for media management, including endpoints for uploading, retrieving, and organizing video content. The backend stores video metadata in a MySQL database and persists video files in a dedicated Docker volume. It also leverages FFmpeg for tasks such as transcoding, thumbnail generation, and format conversion.

## Features
- RESTful API built with Flask-RESTX
- MySQL database for structured metadata
- SQLAlchemy ORM for database interaction
- Alembic for schema migrations
- FFmpeg integration for video processing
- Dockerized deployment with volume-based storage
- Health check endpoint for monitoring
- HLS (Http Live Stream)
- Upload chunked files

## Tech Stack

|Item| Value|
|--|--|
|Framework|Flask-RESTX|
|ORM|SQLAlchemy|
|Migrations|Alembic|
|Database|MySQL|
|Media Processing| FFmpeg|
|Containerization|Docker + Docker Compose|


## Prerequisites
- Docker ≥ 20.x
- Docker Compose ≥ v2.x
- MySQL client (optional for debugging)
- FFmpeg installed in container (already handled in Dockerfile)



## Setup

1. **Clone repository**
```
git clone git@github.com:allandark/VideoStreamerBackend.git
```
2. **Setup secrets**
```
echo "your_root_password" > db_root_password.txt
```

3. **Run with Docker Compose**
```
docker compose up --build -d
```
4. **Access API**
- Default: http://localhost:5000/api

### Environment Variables
Project can be configured in docker compose file
```
environment:
      FLASK_RUN_HOST: "0.0.0.0"
      FLASK_RUN_PORT: 5000
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/db_root_password
      MYSQL_HOST: sql-database
      MYSQL_PORT: 3306
      MYSQL_DATABASE: video_streamer
      N_CONCURRENT_WORKERS: 4
```

### Video Usage
#### Upload Steps
To upload a video in chunks and prepare it for streaming:
1. Create an upload task
    `POST /api/media/task`
    - Purpose: Initializes a chunked upload session.
2. Upload video chunks
    `POST /api/upload/chunk_upload`
    - Purpose: Upload individual chunks of the video file.
3. Complete the upload
    `POST /api/upload/chunk_complete`
    - Purpose: Signals that all chunks have been uploaded successfully.
4. Create HLS build task
    `POST /api/media/task`
    - Purpose: Triggers HLS (HTTP Live Streaming) playlist generation using FFmpeg.
5. Create video metadata resource
    `POST /api/video_meta`
    - Purpose: Stores video metadata in the database.

#### Streaming Workflow
To stream the uploaded video:

1. Retrieve HLS playlist
    `GET /api/media/playlist/{media_id}`
    - Purpose: Returns the .m3u8 playlist file for HLS streaming.







## Database migrations
1. **Setup venv** 
```
python -m venv .venv
<activate_venv>
``` 

2. **Install requirements**

```
pip install -r requirements.txt
```
3. **Generate migrations**
```
alembic revision --autogenerate -m "message"
```
4. **Upload migration to head**
```
alembic upgrade head
```
5. **Check current migration (optional)**
```
alembic current
```
