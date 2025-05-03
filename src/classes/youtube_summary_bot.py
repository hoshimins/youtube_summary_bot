import os
import discord
import requests
from classes.database_manager import DatabaseManager


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

        title = f"# 【要約】\n## {data[0][0]} \n\n"
        message = f"{data[0][1]} \n\n{data[0][2]}"

        content = f"{title}{message}"

        response = requests.post(self.webhook_url, json={"content": content})

        if response.status_code == 204:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")