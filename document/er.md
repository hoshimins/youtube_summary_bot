```mermaid
erDiagram
    channel ||--o{ video : "1対多"
    video ||--|| captions : "1対1"
    video ||--|| summary : "1対1"

    channel {
        varchar(255) channel_id PK
        varchar(255) channel_name
        timestamp created_at
    }

    video {
        varchar(255) video_id PK
        text title
        varchar(255) channel_id FK
        date published
        varchar(255) link
        boolean summary_send_flag
    }

    captions {
        varchar(255) video_id PK_FK
        text caption
        boolean caption_unavailable
        timestamp created_at
        timestamp updated_at
    }

    summary {
        varchar(255) video_id PK_FK
        text summary
        timestamp created_at
        timestamp updated_at
    }
```
