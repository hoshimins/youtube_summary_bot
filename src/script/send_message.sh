#!/bin/bash
cd /home/hoshimi/apps/youtube_summary_bot
source venv/bin/activate
export $(cat .env | xargs)
export PYTHONPATH=/home/hoshimi/apps/youtube_summary_bot/src
python src/bot/main.py
