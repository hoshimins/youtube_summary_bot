import os
import discord
from classes.database_manager import DatabaseManager


class YoutubeSummaryBot(discord.Client):
    def __init__(self, intents: discord.Intents):
        super().__init__(intents=intents)
        self.token = os.getenv("DISCORD_TOKEN")
        self.summary_text_ch = int(os.getenv("SUMMARY_TEXT_CHANNEL_ID"))
        if self.token is None:
            raise ValueError(
                "DISCORD_TOKEN is not set in the environment variables.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        await self.get_summary()

    async def on_message(self, message):
        if message.author == self.user:
            return

    async def get_summary(self):
        db_manager = DatabaseManager()
        summary_data = db_manager.get_not_send_summaries_data()
        if not summary_data:
            return
        await self._send_summary_message_to_forum(summary_data)
        db_manager.update_summary_send_flag(summary_data[0][3])
        db_manager._close()

    async def _send_summary_message_to_forum(self, data):
        summary_text_ch = self.get_channel(self.summary_text_ch)
        if summary_text_ch is None:
            print(f"[ERROR] チャンネルID {self.summary_text_ch} が見つかりません")
            return

        title = f"#【要約】\n ## {data[0][0]} \n\n"
        message = f"> {data[0][1]} \n\n{data[0][2]}"

        content = f"{title}{message}"

        await summary_text_ch.send(
            content=content,
        )
