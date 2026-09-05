# Python 3.12 slim。字幕取得 (latest) 用。
# 要約 (summarize) はホストの Codex CLI を使う想定のため、
# 本番の定期実行はコンテナではなくホスト上の cron / スクリプトを推奨。
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY sql/ ./sql/

ENV PYTHONPATH=src

CMD ["python", "src/main.py", "latest"]
