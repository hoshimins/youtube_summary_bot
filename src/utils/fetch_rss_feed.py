import feedparser
from typing import Dict, List


def get_latest_videos(RSS_URL: str) -> List[Dict[str, str]]:
    """指定したRSSのURLから最新の動画情報を取得する"""
    feed = feedparser.parse(RSS_URL)
    status = getattr(feed, "status", None)
    if status is not None and status >= 400:
        raise RuntimeError(f"RSS取得に失敗しました (HTTP {status}): {RSS_URL}")
    if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
        error = getattr(feed, "bozo_exception", "不正なRSS")
        raise RuntimeError(f"RSSの解析に失敗しました: {error}")
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
