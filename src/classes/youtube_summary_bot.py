import os
import discord
from classes.database_manager import DatabaseManager


class YoutubeSummaryBot(discord.Client):
    def __init__(self, intents: discord.Intents):
        super().__init__(intents=intents)
        self.token = os.getenv("DISCORD_TOKEN")
        self.forum_channel_id = os.getenv("FORUM_CHANNEL_ID")
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
        forum_channel = self.get_channel(self.forum_channel_id)

        if isinstance(forum_channel, discord.ForumChannel):
            title = f"【要約】{data[0][0]}"
            content = f"{data[0][1]} \n\n{data[0][2]}"

            await forum_channel.create_thread(
                name=title,
                content=content,
                auto_archive_duration=10080
            )

        else:
            print("指定されたチャンネルはフォーラムチャンネルではありません。")
