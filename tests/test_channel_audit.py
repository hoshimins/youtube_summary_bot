import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.channel_audit import build_channel_audit, format_audit_report  # noqa: E402


class ChannelAuditTests(unittest.TestCase):
    def test_full_scan_finds_missing_and_db_only_videos(self):
        remote_videos = [
            {
                "video_id": "known",
                "title": "Known",
                "published": "2026-09-03",
                "link": "https://youtu.be/known",
            },
            {
                "video_id": "missing",
                "title": "Missing from DB",
                "published": "2026-09-04",
                "link": "https://youtu.be/missing",
            },
        ]
        db_videos = [
            {
                "video_id": "known",
                "title": "Known",
                "published": "2026-09-03",
                "link": "https://youtu.be/known",
                "caption": "caption",
                "caption_unavailable": False,
                "summary": "summary",
                "summary_send_flag": True,
            },
            {
                "video_id": "deleted",
                "title": "Possibly deleted",
                "published": "2026-09-01",
                "link": "https://youtu.be/deleted",
                "caption": None,
                "caption_unavailable": False,
                "summary": None,
                "summary_send_flag": False,
            },
        ]

        report = build_channel_audit(
            channel_id="UC-test",
            channel_name="Test channel",
            remote_channel_name="Test channel",
            remote_video_count=2,
            remote_videos=remote_videos,
            db_videos=db_videos,
        )

        self.assertEqual(report["matched_count"], 1)
        self.assertEqual([video["video_id"] for video in report["missing_in_db"]], ["missing"])
        self.assertEqual([video["video_id"] for video in report["db_only"]], ["deleted"])
        self.assertEqual(report["status_counts"]["caption_ready"], 1)
        self.assertEqual(report["status_counts"]["caption_pending"], 1)
        self.assertEqual(report["status_counts"]["summary_ready"], 1)
        self.assertEqual(report["status_counts"]["discord_sent"], 1)

    def test_limited_scan_does_not_call_older_db_videos_deleted(self):
        report = build_channel_audit(
            channel_id="UC-test",
            channel_name="Test channel",
            remote_videos=[{"video_id": "latest", "title": "Latest"}],
            db_videos=[{"video_id": "older", "title": "Older"}],
            scan_limit=1,
        )

        self.assertEqual(report["db_only"], [])
        self.assertEqual([video["video_id"] for video in report["outside_scan"]], ["older"])

    def test_text_report_contains_missing_video(self):
        report = build_channel_audit(
            channel_id="UC-test",
            channel_name="Test channel",
            remote_videos=[
                {
                    "video_id": "missing",
                    "title": "未取得動画",
                    "published": "2026-09-05",
                }
            ],
            db_videos=[],
        )

        output = format_audit_report([report])
        self.assertIn("未取得候補（YouTubeにあり / DBになし）: 1 件", output)
        self.assertIn("未取得動画", output)


if __name__ == "__main__":
    unittest.main()
