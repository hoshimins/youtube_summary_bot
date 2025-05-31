#!/bin/bash
cd /home/hoshimi/apps/youtube_summary_bot
source venv/bin/activate
export $(cat .env | xargs)
python src/main.py latest
