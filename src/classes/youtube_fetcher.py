from googleapiclient.discovery import build
import os
from typing import List, Dict


class YoutubeFetcher():
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')

        # YouTube API クライアント初期化
        self.youtube = build("youtube", "v3", developerKey=self.api_key,
                             credentials=None)

    def get_channel_info(self, channel_id: str) -> Dict[str, object]:
        """チャンネル名・公開動画数・アップロード一覧を取得する。"""
        response = self.youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_id,
        ).execute()

        if not response.get("items"):
            raise ValueError(f"チャンネルが見つかりません: {channel_id}")

        item = response["items"][0]
        statistics = item.get("statistics", {})
        video_count = statistics.get("videoCount")
        return {
            "channel_id": item.get("id", channel_id),
            "channel_name": item["snippet"]["title"],
            "video_count": int(video_count) if video_count is not None else None,
            "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
        }

    def fetch_all_videos(
        self,
        channel_id: str,
        limit: int | None = None,
        uploads_playlist_id: str | None = None,
    ) -> List[Dict[str, str]]:
        """指定チャンネルの動画を新しい順に取得する。limit=None で全件。"""
        if limit is not None and limit <= 0:
            raise ValueError("limit は 1 以上、または None を指定してください")
        playlist_id = uploads_playlist_id or self._get_uploads_playlist_id(channel_id)
        return self._get_all_videos_from_playlist(playlist_id, limit=limit)

    def get_video_info(self, video_id: str) -> Dict[str, str]:
        """動画IDから動画情報を取得"""
        response = self.youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if not response["items"]:
            return {}

        item = response["items"][0]["snippet"]
        return {
            "video_id": video_id,
            "title": item["title"],
            "published": item["publishedAt"],
            "link": f'https://www.youtube.com/watch?v={video_id}',
            "channel_id": item["channelId"],
            "channel_name": item.get("channelTitle") or item["channelId"],
        }

    def _get_uploads_playlist_id(self, channel_id: str) -> str:
        """uploadsプレイリストIDを取得"""
        return str(self.get_channel_info(channel_id)["uploads_playlist_id"])

    def _get_all_videos_from_playlist(
        self, playlist_id: str, limit: int | None = None
    ) -> List[Dict[str, str]]:
        """プレイリスト内の全動画を取得"""
        videos: List[Dict[str, str]] = []
        next_page_token: str | None = None

        while True:
            remaining = 50 if limit is None else limit - len(videos)
            response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=min(50, remaining),
                pageToken=next_page_token
            ).execute()

            for item in response["items"]:
                videos.append({
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published": item["snippet"]["publishedAt"],
                    "link": f'https://www.youtube.com/watch?v={item["snippet"]["resourceId"]["videoId"]}'
                })

            if limit is not None and len(videos) >= limit:
                return videos[:limit]

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return videos
