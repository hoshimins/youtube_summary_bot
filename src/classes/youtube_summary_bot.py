import os
import time
import requests
from classes.database_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class YoutubeSummaryBot:
    """Discord Webhook 経由で未送信要約を投稿する。"""

    def __init__(self):
        self.webhook_url = os.getenv("WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("WEBHOOK_URL が設定されていません")

    async def get_summary(self):
        db_manager = DatabaseManager()
        try:
            summary_data = db_manager.get_not_send_summaries_data()
            if not summary_data:
                logger.info("未送信の要約はありません")
                return

            sent = self._send_summary_message(summary_data)
            if sent:
                db_manager.update_summary_send_flag(summary_data[0][3])
            else:
                logger.error(
                    "Discord 送信が完了しなかったため summary_send_flag は更新しません"
                )
        finally:
            db_manager._close()

    def _send_summary_message(self, data) -> bool:
        """全文送信に成功したら True。途中失敗したら False（フラグ更新しない）。"""
        MAX_MESSAGE_LENGTH = 1950

        title = data[0][0].strip()
        summary = data[0][1].strip()
        url = data[0][2].strip()

        intro_message = f"**{title}**\n{url}"
        response = requests.post(self.webhook_url, json={"content": intro_message})
        if response.status_code != 204:
            logger.error(f"イントロ送信失敗: {response.status_code}, {response.text}")
            return False

        chunks = [
            summary[i:i + MAX_MESSAGE_LENGTH]
            for i in range(0, len(summary), MAX_MESSAGE_LENGTH)
        ]
        for idx, chunk in enumerate(chunks, start=1):
            time.sleep(1)
            response = requests.post(self.webhook_url, json={"content": chunk})
            if response.status_code != 204:
                logger.error(
                    f"[{idx}/{len(chunks)}] メッセージ送信失敗: "
                    f"{response.status_code}, {response.text}"
                )
                return False

        logger.info(f"Discord 送信完了: {title}")
        return True
