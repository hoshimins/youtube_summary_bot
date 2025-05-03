from classes import youtube_summary_bot
from utils.config import load_env
import asyncio


async def main():
    load_env()
    bot = youtube_summary_bot.YoutubeSummaryBot()
    await bot.get_summary()


if __name__ == "__main__":
    asyncio.run(main())
