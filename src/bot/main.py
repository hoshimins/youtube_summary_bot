from classes import youtube_summary_bot
from utils.config import load_env
from utils.logger import get_logger
from utils.notify import notify_failure
import asyncio

logger = get_logger(__name__)


async def main():
    load_env()
    bot = youtube_summary_bot.YoutubeSummaryBot()
    await bot.get_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Discord 送信処理で異常終了: {e}")
        notify_failure("Discord 送信 異常終了", str(e))
        raise
