#!/usr/bin/env python3
"""登録チャンネルの YouTube / DB 動画差分を読み取り専用で監査する。"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

from classes.database_manager import DatabaseManager  # noqa: E402
from classes.youtube_fetcher import YoutubeFetcher  # noqa: E402
from utils import fetch_rss_feed  # noqa: E402
from utils.channel_audit import build_channel_audit, format_audit_report  # noqa: E402
from utils.config import load_env  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="登録チャンネルの YouTube 公開動画と DB の差分を調べます（DB変更なし）。"
    )
    parser.add_argument(
        "--channel-id",
        help="指定したチャンネルだけ監査する（省略時は登録済み全チャンネル）",
    )
    parser.add_argument(
        "--source",
        choices=("api", "rss"),
        default="api",
        help="取得元。api は全件監査、rss はAPIキー不要の最新フィード監査（既定: api）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="YouTubeから取得する最新動画数。0 は全件（既定: 0）",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="出力形式（既定: text）",
    )
    return parser


def _safe_error(exc: Exception) -> str:
    """例外文字列から API キーを除去する。"""
    message = str(exc)
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if api_key:
        message = message.replace(api_key, "[redacted]")
    return re.sub(r"([?&]key=)[^&\s\"]+", r"\1[redacted]", message)


def run(args: argparse.Namespace) -> tuple[list[dict], int]:
    if args.limit < 0:
        raise ValueError("--limit は 0 以上で指定してください")

    scan_limit = args.limit or None
    if args.source == "rss":
        # YouTube RSS は通常、最新15件程度しか返さない。
        scan_limit = min(args.limit or 15, 15)

    load_env()
    reports: list[dict] = []
    error_count = 0

    with DatabaseManager() as db:
        channels = db.list_channels()
        if args.channel_id:
            channels = [
                channel
                for channel in channels
                if channel["channel_id"] == args.channel_id
            ]
            if not channels:
                raise ValueError(
                    f"指定されたチャンネルは登録されていません: {args.channel_id}"
                )

        if not channels:
            raise ValueError(
                "登録チャンネルがありません。manage_channels.py add で登録してください"
            )

        fetcher = YoutubeFetcher()
        for channel in channels:
            channel_id = channel["channel_id"]
            channel_name = channel["channel_name"]
            db_videos = []
            try:
                db_videos = db.get_channel_video_audit_data(channel_id)
                if args.source == "api":
                    channel_info = fetcher.get_channel_info(channel_id)
                    remote_videos = fetcher.fetch_all_videos(
                        channel_id,
                        limit=scan_limit,
                        uploads_playlist_id=str(channel_info["uploads_playlist_id"]),
                    )
                    remote_channel_name = str(channel_info["channel_name"])
                    remote_video_count = channel_info["video_count"]
                    full_scan = scan_limit is None
                    scan_description = None
                else:
                    remote_videos = fetch_rss_feed.get_latest_videos(
                        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                    )
                    remote_videos = remote_videos[:scan_limit]
                    remote_channel_name = None
                    remote_video_count = None
                    full_scan = False
                    scan_description = f"RSS最新フィード（最大 {scan_limit} 件）"

                report = build_channel_audit(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    remote_channel_name=remote_channel_name,
                    remote_video_count=remote_video_count,
                    remote_videos=remote_videos,
                    db_videos=db_videos,
                    scan_limit=scan_limit,
                    full_scan=full_scan,
                    scan_description=scan_description,
                )
                report["source"] = args.source
                reports.append(report)
            except Exception as exc:
                error_count += 1
                error_report = build_channel_audit(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    remote_videos=[],
                    db_videos=db_videos,
                    scan_limit=scan_limit,
                    full_scan=False,
                    scan_description="YouTube取得失敗",
                )
                error_report["source"] = args.source
                error_report["error"] = _safe_error(exc)
                reports.append(error_report)

    return reports, error_count


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        reports, error_count = run(args)
    except Exception as exc:
        print(f"監査を開始できません: {_safe_error(exc)}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(reports, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_audit_report(reports))
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
