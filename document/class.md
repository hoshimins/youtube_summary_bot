```mermaid
classDiagram
    class YoutubeFetcher {
        +fetch_video_info(video_id)
        +fetch_video_list(channel_id)
    }

    class CaptionFetcher {
        +get_caption(video_id)
    }

    class SummaryGenerator {
        +generate(caption_text)
    }

    class DatabaseManager {
        +save_caption(video_id, caption_text)
        +save_summary(video_id, summary_text)
        +get_latest_video()
    }
```
