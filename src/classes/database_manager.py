import psycopg2
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_url = os.getenv('DATABASE_URL')
        self._connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _connect(self):
        self.connection = psycopg2.connect(self.db_url)
        self.cursor = self.connection.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    # 後方互換
    def _close(self):
        self.close()

    def _check_db_channel_table(self, channel_id, channel_name):
        """動画保存時の後方互換用。チャンネルを登録・更新する。"""
        self.add_channel(channel_id, channel_name)

    def list_channels(self):
        """登録済みチャンネルを辞書のリストで返す。空でも例外にしない。"""
        self.cursor.execute(
            "SELECT channel_id, channel_name, created_at "
            "FROM youtube_feed_summary.channel "
            "ORDER BY created_at ASC, channel_id ASC"
        )
        rows = self.cursor.fetchall()
        return [
            {
                "channel_id": row[0],
                "channel_name": row[1],
                "created_at": str(row[2]) if row[2] is not None else None,
            }
            for row in rows
        ]

    def add_channel(self, channel_id, channel_name):
        """チャンネルを登録する。既存IDなら表示名を更新する。"""
        channel_id = (channel_id or "").strip()
        channel_name = (channel_name or "").strip()
        if not channel_id:
            raise ValueError("channel_id は必須です")
        if not channel_name:
            raise ValueError("channel_name は必須です")

        try:
            self.cursor.execute(
                """
                INSERT INTO youtube_feed_summary.channel (channel_id, channel_name)
                VALUES (%s, %s)
                ON CONFLICT (channel_id) DO UPDATE
                SET channel_name = EXCLUDED.channel_name
                """,
                (channel_id, channel_name),
            )
            self.connection.commit()
            logger.info(f"channel_id: {channel_id} を登録・更新しました")
        except Exception as e:
            logger.error(f"チャンネル登録エラー: {e}")
            self.connection.rollback()
            raise

    def get_all_channels(self):
        """登録済みチャンネルを全件取得する。"""
        channels = self.list_channels()
        if not channels:
            raise ValueError("channelテーブルにデータが存在しません")
        return [(channel["channel_id"], channel["channel_name"]) for channel in channels]

    def get_channel_data(self):
        """先頭チャンネルを返す（後方互換）。"""
        return self.get_all_channels()[0]

    def get_not_send_summaries_data(self):
        self.cursor.execute(
            "SELECT v.title, s.summary, v.link, v.video_id, v.published "
            "FROM youtube_feed_summary.summary s "
            "JOIN youtube_feed_summary.video v ON s.video_id = v.video_id "
            "WHERE v.summary_send_flag = false AND s.summary IS NOT NULL "
            "ORDER BY v.published"
        )
        return self.cursor.fetchall()

    def update_summary_send_flag(self, video_id):
        self.cursor.execute(
            "UPDATE youtube_feed_summary.video SET summary_send_flag = true WHERE video_id = %s", (video_id,))
        self.connection.commit()

    def get_db_data(self, channel_id):
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_feed_summary.video WHERE channel_id = %s ORDER BY published DESC", (channel_id,))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"動画データ取得エラー: {e}")
            self.connection.rollback()
            raise

    def get_channel_video_audit_data(self, channel_id):
        """監査用に動画と字幕・要約の状態をまとめて取得する。"""
        try:
            self.cursor.execute(
                """
                SELECT
                    v.video_id,
                    v.title,
                    v.published,
                    v.link,
                    cp.caption,
                    cp.caption_unavailable,
                    s.summary,
                    v.summary_send_flag
                FROM youtube_feed_summary.video v
                LEFT JOIN youtube_feed_summary.captions cp
                    ON cp.video_id = v.video_id
                LEFT JOIN youtube_feed_summary.summary s
                    ON s.video_id = v.video_id
                WHERE v.channel_id = %s
                ORDER BY v.published DESC, v.video_id ASC
                """,
                (channel_id,),
            )
            rows = self.cursor.fetchall()
            return [
                {
                    "video_id": row[0],
                    "title": row[1],
                    "published": str(row[2]) if row[2] is not None else None,
                    "link": row[3],
                    "caption": row[4],
                    "caption_unavailable": bool(row[5]),
                    "summary": row[6],
                    "summary_send_flag": bool(row[7]),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"動画監査データ取得エラー: {e}")
            self.connection.rollback()
            raise

    def get_none_caption_record(self):
        """caption が NULL かつ取得不可フラグが立っていないレコードを全件取得"""
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_feed_summary.captions cp "
                "JOIN youtube_feed_summary.video v ON cp.video_id = v.video_id "
                "WHERE cp.caption IS NULL AND cp.caption_unavailable = FALSE"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"未取得字幕レコード取得エラー: {e}")
            self.connection.rollback()
            raise

    def mark_caption_unavailable(self, video_id):
        """字幕取得不可フラグを立てる（以後スキップ対象）"""
        try:
            self.cursor.execute(
                "UPDATE youtube_feed_summary.captions SET caption_unavailable = TRUE, updated_at = NOW() WHERE video_id = %s",
                (video_id,)
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"字幕不可フラグ更新エラー (video_id={video_id}): {e}")
            self.connection.rollback()
            raise

    def get_none_summary_record(self):
        """caption 取得済みで summary が NULL のレコードを全件取得"""
        try:
            self.cursor.execute("""
                SELECT s.video_id, cp.caption
                FROM youtube_feed_summary.summary s
                JOIN youtube_feed_summary.captions cp ON s.video_id = cp.video_id
                WHERE s.summary IS NULL AND cp.caption IS NOT NULL
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"未生成要約レコード取得エラー: {e}")
            self.connection.rollback()
            raise

    def save_caption_data(self, video_id, caption):
        """字幕データ保存"""
        try:
            self.cursor.execute(
                "UPDATE youtube_feed_summary.captions SET caption = %s, updated_at = NOW() WHERE video_id = %s",
                (caption, video_id)
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"字幕データ保存エラー (video_id={video_id}): {e}")
            self.connection.rollback()
            raise

    def save_summary_data(self, video_id, summary):
        """要約データ保存"""
        try:
            self.cursor.execute(
                "UPDATE youtube_feed_summary.summary SET summary = %s, updated_at = NOW() WHERE video_id = %s",
                (summary, video_id)
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"要約データ保存エラー (video_id={video_id}): {e}")
            self.connection.rollback()
            raise

    def save_db_new_data(self, data, channel_id, channel_name):
        """動画データ保存（video 全部, caption, summary はvideo_idだけ生成）"""
        self._check_db_channel_table(channel_id, channel_name)

        try:
            for video in data:
                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.video (video_id, title, channel_id, published, link) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (video['video_id'], video['title'], channel_id,
                     video['published'], video['link'])
                )

                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.captions (video_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (video['video_id'],)
                )

                self.cursor.execute(
                    "INSERT INTO youtube_feed_summary.summary (video_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (video['video_id'],)
                )

            self.connection.commit()
        except Exception as e:
            logger.error(f"動画データ保存エラー: {e}")
            self.connection.rollback()
            raise
