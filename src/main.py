import os
import sys
import time
from youtube_transcript_api._errors import IpBlocked, RequestBlocked
from utils import fetch_rss_feed
from utils import comparison_data
from utils import get_caption
from utils import get_summary
from utils.config import load_env
from utils.logger import get_logger
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

    for video_id in no_caption_video_id:
        try:
            caption_txt = get_caption.get_caption(video_id)
        except (IpBlocked, RequestBlocked):
            logger.error("YouTube に IP ブロックされています。時間をおいてから再実行してください。")
            break
        time.sleep(sleep_interval)
        if caption_txt is None:
            logger.warning(f"字幕が取得できなかったためスキップします: {video_id}")
            continue

        dbManager.save_caption_data(video_id, caption_txt)
        logger.info(f"キャプションデータを保存しました: {video_id}")


def generate_summaries(dbManager):
    """要約生成（LM Studio 依存）"""
    no_summary_record = dbManager.get_none_summary_record()
    if not no_summary_record:
        logger.info("要約が未生成のレコードはありません")
        return

    logger.info(f"要約未生成の動画: {len(no_summary_record)} 件")

    for video_id, caption_txt in no_summary_record:
        summary_text = get_summary.get_summary(caption_txt)
        dbManager.save_summary_data(video_id, summary_text)
        logger.info(f"要約データを保存しました: {video_id}")


def get_data(mode, dbManager):
    """指定されたモードによって動画情報を取得する"""

    if mode == "latest":
        channel_id, channel_name = dbManager.get_channel_data()
        RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        new_data = fetch_rss_feed.get_latest_videos(RSS_URL)
        db_data = dbManager.get_db_data(channel_id)
        new_data = comparison_data.compare_data(db_data, new_data)

        if not new_data:
            logger.info("新しい動画はありません")
            return

        logger.info(f"新しい動画は {len(new_data)} 件です")
        dbManager.save_db_new_data(new_data, channel_id, channel_name)

    elif mode == "all":
        channel_id, channel_name = dbManager.get_channel_data()
        youtube_fetcher = YoutubeFetcher()
        new_data = youtube_fetcher.fetch_all_videos(channel_id)
        dbManager.save_db_new_data(new_data, channel_id, channel_name)

    else:
        channel_id, channel_name = dbManager.get_channel_data()
        youtube_fetcher = YoutubeFetcher()
        new_data = youtube_fetcher.get_video_info(mode)
        dbManager.save_db_new_data([new_data], channel_id, channel_name)


if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 1:
        logger.error("引数が不足しています")
        sys.exit(1)

    load_env()
    dbManager = DatabaseManager()

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
