import os
import discord
import requests
from classes.database_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class YoutubeSummaryBot(discord.Client):

    def __init__(self):
        self.webhook_url = os.getenv("WEBHOOK_URL")
        self.summary_text_ch = int(os.getenv("SUMMARY_TEXT_CHANNEL_ID"))

    async def get_summary(self):
        db_manager = DatabaseManager()
        summary_data = db_manager.get_not_send_summaries_data()
        if not summary_data:
            return
        await self._send_summary_message(summary_data)
        db_manager.update_summary_send_flag(summary_data[0][3])
        db_manager._close()

    async def _send_summary_message(self, data):
        MAX_MESSAGE_LENGTH = 1950

        title = data[0][0].strip()
        summary = data[0][1].strip()
        url = data[0][2].strip()

        intro_message = f"**{title}**\n{url}"
        response = requests.post(self.webhook_url, json={"content": intro_message})
        if response.status_code != 204:
            logger.error(f"イントロ送信失敗: {response.status_code}, {response.text}")
            return

        chunks = [summary[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
        for idx, chunk in enumerate(chunks, start=1):
            response = requests.post(self.webhook_url, json={"content": chunk})
            if response.status_code != 204:
                logger.error(f"[{idx}/{len(chunks)}] メッセージ送信失敗: {response.status_code}, {response.text}")
                break

        logger.info(f"Discord 送信完了: {title}")
