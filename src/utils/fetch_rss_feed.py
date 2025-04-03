import feedparser
from typing import Dict


def get_latest_videos(RSS_URL: str) -> Dict[str, str]:
    """指定したRSSのURLから最新の動画情報を取得する"""
    feed = feedparser.parse(RSS_URL)
    videos = []
    for entry in feed.entries:
        video_id = entry.yt_videoid
        title = entry.title
        published = entry.published
        link = entry.link
        videos.append({
            "video_id": video_id,
            "title": title,
            "published": published,
            "link": link
        })

    return videos
