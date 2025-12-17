# ER-Diagram

## Video DB

```mermaid
erDiagram

    VIDEO_META_DATA ||--|| MEDIA_META_DATA : has

    VIDEO_TAG ||--o{ TAG : descripes
    VIDEO_TAG ||--o{ VIDEO_META_DATA : descripes

    VIDEO_STAR ||--o{ STAR : features
    VIDEO_STAR ||--o{ VIDEO_META_DATA : features

    VIDEO_DIRECTOR ||--o{ DIRECTOR : produces
    VIDEO_DIRECTOR ||--o{ VIDEO_META_DATA : produces

    VIDEO_GENRE ||--o{ GENRE : categorizes
    VIDEO_GENRE ||--o{ VIDEO_META_DATA : categorizes

    VIDEO_SERIES ||--o{ SERIES : contains
    VIDEO_SERIES ||--o{ VIDEO_META_DATA : contains

    VIDEO_META_DATA{
        int id PK
        int media_id FK
        string title    
        string description     
        int duration_seconds     
        float rating
        int views
        date upload_date        
    }

    MEDIA_META_DATA{
        int id PK
        int video_id FK
        string name
        string hash  
        string mimetype
        bool master_file
        json video_tracks 
        json audio_tracks 
        json subtitle_tracks 
        bool thumbnail
    }


    DIRECTOR{
        int id PK
        string full_name  
        float rating
    }

    STAR{
        int id PK
        string full_name  
        float rating
    }

    SERIES{
        int id PK
        string name
        float rating
    }

    GENRE{
        int id PK
        string name 
        float rating 
    }

    TAG{
        int id PK
        string name 
    }

    VIDEO_TAG{
        int video_id FK
        int tag_id FK
    }


    VIDEO_DIRECTOR{
        int video_id FK
        int director_id FK
    }
    VIDEO_STAR{
        int video_id FK
        int star_id FK
    }
    VIDEO_GENRE{
        int video_id FK
        int genre_id FK
    }
    VIDEO_SERIES{
        int video_id FK
        int series_id FK
    }


```

## Managment DB

```mermaid
erDiagram

    USER{
        int id PK
        string hashed_user_name
        string hashed_password
        string hashed_email
        string type
        date creation_date
    }

```