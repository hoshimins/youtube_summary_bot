from googleapiclient.discovery import build
import os
from typing import List, Dict


class YoutubeFetcher():
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')

        # YouTube API クライアント初期化
        self.youtube = build("youtube", "v3", developerKey=self.api_key,
                             credentials=None)

    def fetch_all_videos(self, channel_id: str) -> List[Dict[str, str]]:
        """指定チャンネルの全動画を取得"""
        playlist_id = self._get_uploads_playlist_id(channel_id)
        return self._get_all_videos_from_playlist(playlist_id)

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
            "link": f'https://www.youtube.com/watch?v={video_id}'
        }

    def _get_uploads_playlist_id(self, channel_id: str) -> str:
        """uploadsプレイリストIDを取得"""
        response = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def _get_all_videos_from_playlist(self, playlist_id: str) -> List[Dict[str, str]]:
        """プレイリスト内の全動画を取得"""
        videos: List[Dict[str, str]] = []
        next_page_token: str | None = None

        while True:
            response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            for item in response["items"]:
                videos.append({
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published": item["snippet"]["publishedAt"],
                    "link": f'https://www.youtube.com/watch?v={item["snippet"]["resourceId"]["videoId"]}'
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return videos
