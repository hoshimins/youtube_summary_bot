import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.caption_text import prepare_caption_for_storage  # noqa: E402
from utils.comparison_data import compare_data, filter_new_videos  # noqa: E402
from utils.notify import notify_failure  # noqa: E402


class CaptionTextTests(unittest.TestCase):
    def test_normalizes_whitespace(self):
        self.assertEqual(prepare_caption_for_storage("  a   b\n c  "), "a b c")

    def test_truncates_by_env(self):
        with patch.dict(os.environ, {"CAPTION_MAX_CHARS": "5"}):
            self.assertEqual(prepare_caption_for_storage("abcdefgh"), "abcde")


class ComparisonDataTests(unittest.TestCase):
    def test_filters_new_videos_by_id(self):
        remote_videos = [
            {"video_id": "old", "title": "Changed title"},
            {"video_id": "new", "title": "New"},
        ]
        result = filter_new_videos({"old"}, remote_videos)
        self.assertEqual([video["video_id"] for video in result], ["new"])

    def test_returns_only_new_videos(self):
        db_data = [
            ("old1", "Old", "ch", "2024-01-01", "https://example.com/old1", False),
        ]
        new_data = [
            {
                "video_id": "old1",
                "title": "Old",
                "published": "2024-01-01T00:00:00+00:00",
                "link": "https://example.com/old1",
            },
            {
                "video_id": "new1",
                "title": "New",
                "published": "2024-02-01T00:00:00+00:00",
                "link": "https://example.com/new1",
            },
        ]
        result = compare_data(db_data, new_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["video_id"], "new1")


class NotifyTests(unittest.TestCase):
    def test_noop_without_url(self):
        with patch.dict(os.environ, {"NTFY_URL": ""}, clear=False):
            os.environ.pop("NTFY_URL", None)
            self.assertFalse(notify_failure("t", "m"))

    def test_posts_when_url_set(self):
        mock_response = MagicMock(status_code=200, text="ok")
        with patch.dict(
            os.environ,
            {"NTFY_URL": "https://ntfy.example/test", "NTFY_TOKEN": "secret"},
            clear=False,
        ):
            with patch("utils.notify.requests.post", return_value=mock_response) as post:
                self.assertTrue(notify_failure("hello", "world"))
                post.assert_called_once()
                kwargs = post.call_args.kwargs
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
                self.assertEqual(kwargs["headers"]["Title"], "hello")


if __name__ == "__main__":
    unittest.main()
