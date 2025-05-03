import psycopg2
import os


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_url = os.getenv('DATABASE_URL')
        self._connect()

    def _connect(self):
        self.connection = psycopg2.connect(self.db_url)
        self.cursor = self.connection.cursor()

    def _close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def _check_db_channel_table(self, channel_id, channel_name):
        """チャンネルテーブルの確認&チャンネルテーブルにデータがない場合は挿入"""
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_feed_summary.channel WHERE channel_id = %s", (channel_id,))
            rows = self.cursor.fetchall()

            if not rows:
                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.channel (channel_id, channel_name) VALUES (%s, %s)", (channel_id, channel_name))
                self.connection.commit()
                print(
                    f"Inserted channel_id: {channel_id} into youtube_feed_summary.channel")
            else:
                print(f"Channel ID {channel_id} already exists in the table.")

        except Exception as e:
            print("Error:", e)
            self.connection.rollback()
            self._close()

    def get_channel_data(self):
        self.cursor.execute(
            "SELECT * FROM youtube_feed_summary.channel LIMIT 1")
        row = self.cursor.fetchall()

        if row:
            return row[0][0], row[0][1]
        else:
            raise ValueError("channelテーブルにデータが存在しません")

    def get_not_send_summaries_data(self):
        self.cursor.execute("SELECT v.title, s.summary, v.link, v.video_id FROM youtube_feed_summary.summary s JOIN youtube_feed_summary.video v ON s.video_id = v.video_id WHERE v.summary_send_flag = false AND s.summary IS NOT NULL LIMIT 1")
        rows = self.cursor.fetchall()
        return rows

    def update_summary_send_flag(self, video_id):
        self.cursor.execute(
            "UPDATE youtube_feed_summary.video SET summary_send_flag = true WHERE video_id = %s", (video_id,))
        self.connection.commit()

    def get_db_data(self, channel_id):
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_feed_summary.video WHERE channel_id = %s ORDER BY published DESC", (channel_id,))
            rows = self.cursor.fetchall()
            return rows

        except Exception as e:
            print("Error:", e)
            self.connection.rollback()
            self._close()

    def get_none_caption_record(self):
        """字幕テーブルの確認&字幕テーブルにデータがない場合は挿入"""
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_feed_summary.captions cp JOIN youtube_feed_summary.video v ON cp.video_id = v.video_id WHERE cp.caption IS NULL LIMIT 1")
            rows = self.cursor.fetchall()
            return rows

        except Exception as e:
            print("Error:", e)
            self.connection.rollback()
            self._close()

    def save_caption_data(self, video_id, caption):
        """字幕データ保存"""
        try:
            self.cursor.execute(
                "UPDATE youtube_feed_summary.captions SET caption = %s, updated_at = NOW() WHERE video_id = %s",
                (caption, video_id)
            )

            self.connection.commit()
        except Exception as e:
            print("Error:", e)
            self.connection.rollback()

    def save_summary_data(self, video_id, summary):
        """要約データ保存"""
        try:
            self.cursor.execute(
                "UPDATE youtube_feed_summary.summary SET summary = %s, updated_at = NOW() WHERE video_id = %s",
                (summary, video_id)
            )

            self.connection.commit()
        except Exception as e:
            print("Error:", e)
            self.connection.rollback()

    def save_db_new_data(self, data, channel_id, channel_name):
        """動画データ保存（video 全部, caption, summary はvideo_idだけ生成）"""
        self._check_db_channel_table(channel_id, channel_name)

        try:
            for video in data:
                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.video (video_id, title, channel_id, published, link) VALUES (%s, %s, %s, %s, %s)",
                    (video['video_id'], video['title'], channel_id,
                     video['published'], video['link'])
                )

                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.captions (video_id) VALUES (%s)",
                    (video['video_id'],)
                )

                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.summary (video_id) VALUES (%s)",
                    (video['video_id'],)
                )

            self.connection.commit()
        except Exception as e:
            print("Error:", e)
            self.connection.rollback()
            print("Rollback executed")
            self._close()
