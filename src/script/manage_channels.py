#!/usr/bin/env python3
"""監視対象チャンネルの登録・一覧表示を行う。"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

from classes.database_manager import DatabaseManager  # noqa: E402
from classes.youtube_fetcher import YoutubeFetcher  # noqa: E402
from utils.config import load_env  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="監視対象 YouTube チャンネルを管理します。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="登録済みチャンネルを表示")

    add_parser = subparsers.add_parser("add", help="チャンネルを登録・更新")
    add_parser.add_argument("channel_id", help="YouTube のチャンネルID（UC...）")
    add_parser.add_argument(
        "channel_name",
        nargs="?",
        help="表示名。省略時は YouTube Data API から取得（APIキーが必要）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    load_env()

    with DatabaseManager() as db:
        if args.command == "list":
            channels = db.list_channels()
            if not channels:
                print("登録チャンネルはありません")
                return 0
            for channel in channels:
                print(
                    f"{channel['channel_id']}\t{channel['channel_name']}\t"
                    f"{channel['created_at'] or ''}"
                )
            return 0

        channel_name = args.channel_name
        if not channel_name:
            channel_info = YoutubeFetcher().get_channel_info(args.channel_id)
            channel_name = str(channel_info["channel_name"])

        db.add_channel(args.channel_id, channel_name)
        print(f"登録しました: {channel_name} ({args.channel_id})")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"チャンネル管理に失敗しました: {exc}", file=sys.stderr)
        raise SystemExit(1)
