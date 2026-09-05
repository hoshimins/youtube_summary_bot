import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import sync_videos  # noqa: E402


class FakeDatabaseManager:
    def __init__(self):
        self.saved = []

    def get_all_channels(self):
        return [("UC-test", "Test channel")]

    def get_video_ids(self, channel_id):
        self.requested_channel_id = channel_id
        return {"old"}

    def save_db_new_data(self, videos, channel_id, channel_name):
        self.saved.append((videos, channel_id, channel_name))


class PipelineModeTests(unittest.TestCase):
    def test_sync_videos_only_registers_missing_video_ids(self):
        db = FakeDatabaseManager()
        remote_videos = [
            {"video_id": "old", "title": "Updated title"},
            {"video_id": "new", "title": "New video"},
        ]

        with patch("main.YoutubeFetcher") as fetcher_class:
            fetcher_class.return_value.fetch_all_videos.return_value = remote_videos
            total = sync_videos(db)

        self.assertEqual(total, 1)
        self.assertEqual(db.saved[0][0], [remote_videos[1]])
        fetcher_class.return_value.fetch_all_videos.assert_called_once_with("UC-test")


if __name__ == "__main__":
    unittest.main()
