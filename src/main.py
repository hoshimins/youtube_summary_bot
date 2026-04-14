import os
import sys
import time
from utils import fetch_rss_feed
from utils import comparison_data
from utils import get_caption
from utils import get_summary
from utils.config import load_env
from utils.logger import get_logger
from classes.database_manager import DatabaseManager
from classes.youtube_fetcher import YoutubeFetcher

logger = get_logger(__name__)


def main(mode):
    load_env()
    dbManager = DatabaseManager()
    get_data(mode, dbManager)

    no_caption_record = dbManager.get_none_caption_record()
    if not no_caption_record:
        logger.info("caption が NULL のレコードはありません")
        return

    no_caption_video_id = [record[0] for record in no_caption_record]
    sleep_interval = int(os.getenv("CAPTION_SLEEP_INTERVAL", "30"))

    for video_id in no_caption_video_id:
        caption_txt = get_caption.get_caption(video_id)
        time.sleep(sleep_interval)
        if caption_txt is None:
            logger.warning(f"字幕が取得できなかったためスキップします: {video_id}")
            continue

        dbManager.save_caption_data(video_id, caption_txt)
        logger.info(f"キャプションデータを保存しました: {video_id}")

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

    if args[1] == "all":
        mode = "all"
    elif args[1] == "latest":
        mode = "latest"
    elif args[1] == "id":
        mode = args[2]
    else:
        logger.error("不正な引数です")
        sys.exit(1)

    logger.info(f"mode: {mode} で実行します")
    main(mode)
