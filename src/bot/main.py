import discord
from classes import youtube_summary_bot
from utils.config import load_env


def main():
    load_env()
    intents = discord.Intents.default()
    intents.message_content = True
    bot = youtube_summary_bot.YoutubeSummaryBot(intents=intents)
    bot.run(bot.TOKEN)


if __name__ == "__main__":
    main()
