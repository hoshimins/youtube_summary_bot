import sys
from utils import fetch_rss_feed
from utils import comparison_data
from utils import get_caption
from utils import get_summary
from utils.config import load_env
from classes.database_manager import DatabaseManager
from classes.youtube_fetcher import YoutubeFetcher


def main(mode):
    load_env()
    dbManager = DatabaseManager()
    get_data(mode, dbManager)

    return
    no_caption_record = dbManager.get_none_caption_record()
    if not no_caption_record:
        print("captionsがないレコードはありません")
        return

    no_caption_video_id = [record[0] for record in no_caption_record]

    caption_txt = get_caption.get_caption(no_caption_video_id[0])

    dbManager.save_caption_data(no_caption_video_id[0], caption_txt)
    print("キャプションデータを保存しました")

    summary_text = get_summary.get_summary(caption_txt)

    dbManager.save_summary_data(no_caption_video_id[0], summary_text)
    print("要約データを保存しました")


def get_data(mode, dbManager):
    """指定されたモードによって動画情報を取得する"""

    if mode == "latest":
        channel_id, channel_name = dbManager.get_channel_data()
        RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        new_data = fetch_rss_feed.get_latest_videos(RSS_URL)
        db_data = dbManager.get_db_data(channel_id)
        new_data = comparison_data.compare_data(db_data, new_data)

        if not new_data:
            print("新しい動画はありません")
            return

        print(f"新しい動画は {len(new_data)} 件です")
        dbManager.save_db_new_data(new_data, channel_id, channel_name)

    elif mode == "all":
        youtube_fetcher = YoutubeFetcher()
        new_data = youtube_fetcher.fetch_all_videos('UCCiOsYX3Q3wtgvtep-x_yjA')
        dbManager.save_db_new_data(new_data, channel_id, channel_name)

    else:
        channel_id, channel_name = dbManager.get_channel_data()
        youtube_fetcher = YoutubeFetcher()
        new_data = youtube_fetcher.get_video_info(mode)
        dbManager.save_db_new_data([new_data], channel_id, channel_name)


if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 1:
        print("引数が不足しています")
        sys.exit(1)

    if args[1] == "all":
        mode = "all"
    elif args[1] == "latest":
        mode = "latest"
    elif args[1] == "id":
        mode = args[2]
    else:
        print("不正な引数です")
        sys.exit(1)

    print(f"mode: {mode} で実行します")
    main(mode)
