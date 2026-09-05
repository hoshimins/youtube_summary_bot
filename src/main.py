import os
import sys
import time
from youtube_transcript_api._errors import IpBlocked, RequestBlocked
from utils import fetch_rss_feed
from utils import comparison_data
from utils import get_caption
from utils import get_summary
from utils.caption_text import prepare_caption_for_storage
from utils.config import load_env
from utils.logger import get_logger
from utils.notify import notify_failure
from classes.database_manager import DatabaseManager
from classes.youtube_fetcher import YoutubeFetcher

logger = get_logger(__name__)


def fetch_captions(mode, dbManager):
    """動画情報取得 + 字幕取得（YouTube 依存）"""
    get_data(mode, dbManager)

    no_caption_record = dbManager.get_none_caption_record()
    if not no_caption_record:
        logger.info("caption が NULL のレコードはありません")
        return

    no_caption_video_id = [record[0] for record in no_caption_record]
    sleep_interval = int(os.getenv("CAPTION_SLEEP_INTERVAL", "30"))

    for index, video_id in enumerate(no_caption_video_id):
        try:
            caption_txt = get_caption.get_caption(video_id)
        except (IpBlocked, RequestBlocked) as e:
            msg = "YouTube に IP ブロックされています。時間をおいてから再実行してください。"
            logger.error(msg)
            notify_failure("字幕取得ブロック", f"{msg}\nvideo_id={video_id}\n{e}")
            break

        if caption_txt is None:
            logger.warning(f"字幕が取得できなかったためスキップします: {video_id}")
            dbManager.mark_caption_unavailable(video_id)
        else:
            caption_txt = prepare_caption_for_storage(caption_txt)
            if not caption_txt:
                logger.warning(f"字幕が空のためスキップします: {video_id}")
                dbManager.mark_caption_unavailable(video_id)
            else:
                dbManager.save_caption_data(video_id, caption_txt)
                logger.info(
                    f"キャプションデータを保存しました: {video_id} ({len(caption_txt)} 文字)"
                )

        if index < len(no_caption_video_id) - 1:
            time.sleep(sleep_interval)


def generate_summaries(dbManager):
    """要約生成（SUMMARY_PROVIDER: codex / openai / lmstudio）"""
    no_summary_record = dbManager.get_none_summary_record()
    if not no_summary_record:
        logger.info("要約が未生成のレコードはありません")
        return

    batch_limit = int(os.getenv("SUMMARIZE_BATCH_LIMIT", "3"))
    if batch_limit > 0:
        total = len(no_summary_record)
        no_summary_record = no_summary_record[:batch_limit]
        logger.info(
            f"要約未生成の動画: {total} 件中 {len(no_summary_record)} 件を処理 "
            f"(SUMMARIZE_BATCH_LIMIT={batch_limit})"
        )
    else:
        logger.info(f"要約未生成の動画: {len(no_summary_record)} 件（上限なし）")

    failures = []
    for video_id, caption_txt in no_summary_record:
        try:
            summary_text = get_summary.get_summary(caption_txt)
        except Exception as e:
            logger.error(f"要約生成に失敗しました (video_id={video_id}): {e}")
            failures.append(f"{video_id}: {e}")
            continue

        dbManager.save_summary_data(video_id, summary_text)
        logger.info(f"要約データを保存しました: {video_id}")

    if failures:
        notify_failure(
            "要約生成失敗",
            f"{len(failures)} 件の要約に失敗しました:\n" + "\n".join(failures),
        )


def get_data(mode, dbManager):
    """指定されたモードによって動画情報を取得する"""

    if mode == "latest":
        for channel_id, channel_name in dbManager.get_all_channels():
            logger.info(f"チャンネル処理中: {channel_name} ({channel_id})")
            RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            new_data = fetch_rss_feed.get_latest_videos(RSS_URL)
            db_data = dbManager.get_db_data(channel_id)
            new_data = comparison_data.compare_data(db_data, new_data)

            if not new_data:
                logger.info(f"新しい動画はありません: {channel_name}")
                continue

            logger.info(f"新しい動画は {len(new_data)} 件です: {channel_name}")
            dbManager.save_db_new_data(new_data, channel_id, channel_name)

    elif mode == "all":
        youtube_fetcher = YoutubeFetcher()
        for channel_id, channel_name in dbManager.get_all_channels():
            logger.info(f"チャンネル全動画取得: {channel_name} ({channel_id})")
            new_data = youtube_fetcher.fetch_all_videos(channel_id)
            dbManager.save_db_new_data(new_data, channel_id, channel_name)

    else:
        youtube_fetcher = YoutubeFetcher()
        new_data = youtube_fetcher.get_video_info(mode)
        if not new_data or not new_data.get("video_id"):
            logger.error(f"動画情報を取得できませんでした: {mode}")
            return
        channel_id = new_data["channel_id"]
        channel_name = new_data["channel_name"]
        dbManager.save_db_new_data([new_data], channel_id, channel_name)


if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 1:
        logger.error("引数が不足しています")
        sys.exit(1)

    load_env()
    try:
        with DatabaseManager() as dbManager:
            if args[1] == "summarize":
                logger.info("mode: summarize で実行します")
                generate_summaries(dbManager)

            elif args[1] in ("all", "latest"):
                logger.info(f"mode: {args[1]} で実行します")
                fetch_captions(args[1], dbManager)

            elif args[1] == "id":
                if len(args) <= 2:
                    logger.error("id モードには video_id が必要です")
                    sys.exit(1)
                logger.info(f"mode: id ({args[2]}) で実行します")
                fetch_captions(args[2], dbManager)

            else:
                logger.error("不正な引数です")
                sys.exit(1)
    except Exception as e:
        logger.exception(f"実行中に予期しないエラー: {e}")
        notify_failure("youtube_summary_bot 異常終了", str(e))
        sys.exit(1)
