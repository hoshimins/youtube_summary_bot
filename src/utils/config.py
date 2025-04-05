import os
from dotenv import load_dotenv

_LOADED = False


def load_env():
    """.env を1度だけ読み込む"""
    global _LOADED
    if not _LOADED:
        current_dir = os.getcwd()
        env_file_path = os.path.join(current_dir, ".env")
        load_dotenv(env_file_path)
        _LOADED = True
