# YouTube Summary Bot

YouTube 動画の字幕を自動取得し、AI（デフォルト: Codex CLI）で要約して Discord に投稿する自動化 Bot です。

## 概要

1. YouTube チャンネルの RSS（または Data API）から動画を監視
2. 字幕を取得して PostgreSQL に保存（長文は文字数制限で切り詰め）
3. ホスト上の Codex CLI（または OpenAI / LM Studio）で要約
4. Discord Webhook で投稿（1 実行 1 件）

## 主要機能

- RSS / YouTube Data API による動画取得
- `youtube-transcript-api` による字幕取得（言語は `CAPTION_LANGUAGES`）
- 字幕取得不可フラグ（`caption_unavailable`）
- 要約プロバイダー切替: `codex` / `openai` / `lmstudio`
- Discord Webhook 分割送信とレート制限対策

## システム要件

- Python 3.12 推奨
- PostgreSQL
- YouTube Data API v3 キー（`all` / `id` モード時）
- **要約用**: ホストにインストール済みの Codex CLI（推奨）または OpenAI / LM Studio
- Discord Webhook URL

> 開発は MacBook、本番定期実行は自宅サーバー上の Codex を想定しています。GPU 付き Windows 上の LM Studio は任意のフォールバックです。

## セットアップ

```bash
git clone <repository-url>
cd youtube_summary_bot

uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

psql -U your_user -d your_database -f sql/create.sql
# 既存 DB の場合
psql -U your_user -d your_database -f sql/migrate_2026_09_align_schema.sql

cp .env.example .env
# .env を編集
```

### 環境変数（抜粋）

```bash
DATABASE_URL=postgresql://user:password@host:port/database
YOUTUBE_API_KEY=your_youtube_api_key

SUMMARY_PROVIDER=codex
CODEX_BIN=codex
CODEX_TIMEOUT=600
SUMMARIZE_BATCH_LIMIT=3

WEBHOOK_URL=your_discord_webhook_url
SUMMARY_TEXT_CHANNEL_ID=0

CAPTION_LANGUAGES=en
CAPTION_SLEEP_INTERVAL=30
CAPTION_MAX_CHARS=100000
```

既存 DB には初回だけマイグレーションを適用してください。

```bash
psql -U your_user -d your_database -f sql/migrate_2026_09_align_schema.sql
```

失敗通知を使う場合は ntfy トピック URL を設定します。

```bash
NTFY_URL=https://ntfy.example.com/youtube-summary-bot
# NTFY_TOKEN=optional_bearer_token
```

## 使い方

```bash
source .venv/bin/activate
```

### Step 1: 字幕取得

```bash
PYTHONPATH=src python src/main.py latest
PYTHONPATH=src python src/main.py all
PYTHONPATH=src python src/main.py id VIDEO_ID
```

### Step 2: 要約生成（Codex 利用時はホストで実行）

```bash
PYTHONPATH=src python src/main.py summarize
```

### Step 3: Discord 送信

```bash
PYTHONPATH=src python src/bot/main.py
```

### シェルスクリプト（Step 1 + 2）

```bash
./src/script/get_summary_latest.sh
./src/script/send_message.sh
```

## Cron 設定例

```cron
0 * * * * /path/to/youtube_summary_bot/src/script/get_summary_latest.sh >> /path/to/youtube_summary_bot/summary.log 2>&1
30 * * * * /path/to/youtube_summary_bot/src/script/send_message.sh >> /path/to/youtube_summary_bot/send.log 2>&1
```

## Docker について

`Dockerfile` は **字幕取得（`latest`）向けの参考イメージ**です。

| 処理 | 推奨実行場所 |
|------|----------------|
| `latest` / `all` / `id` | ホストまたはコンテナ可 |
| `summarize`（Codex） | **ホスト必須**（`codex` バイナリとログイン状態） |
| Discord 送信 | ホスト推奨 |

本番の定期実行は `src/script/*.sh` + cron を推奨します。

```bash
docker build -t youtube-summary-bot .
docker run --env-file .env youtube-summary-bot
```

## 技術スタック

| ライブラリ | 用途 |
|-----------|------|
| requests | Discord Webhook HTTP 送信 |
| feedparser | RSS |
| google-api-python-client | YouTube Data API |
| openai | OpenAI / LM Studio 互換 API |
| psycopg2-binary | PostgreSQL |
| youtube-transcript-api | 字幕取得 |
| Codex CLI（外部） | デフォルトの要約エンジン |

## 処理フロー

1. `latest`: 新着検出 → 字幕保存（必要なら切り詰め）
2. `summarize`: 未要約を Codex 等で生成
3. `bot/main.py`: 未送信 1 件を Discord へ

詳細は [CLAUDE.md](./CLAUDE.md) と `document/` を参照。

## 注意事項

- 長い字幕は `CAPTION_MAX_CHARS` で切り詰めます（DB 保存失敗やコンテキスト超過の緩和）
- 字幕言語が無い動画はスキップされ、`caption_unavailable` が立ちます
- Discord はレート制限対策で 1 実行 1 動画です。送信失敗時はフラグを更新しません
- `summarize` は `SUMMARIZE_BATCH_LIMIT`（既定 3）件までに制限されます
- `channel` は複数登録可能。`latest` / `all` は全件を順に処理します

## Makefile

```bash
make run              # latest
make run MODE=all
make run MODE=summarize
make test             # ローカル単体テスト（GitHub Actions なし）
```

## 今後の拡張案

- マルチチャンネル対応
- Discord Bot 化
- 要約プロバイダーの自動フェイルオーバー
- 失敗時の ntfy 等通知

## ライセンス

プロジェクトオーナーに確認してください。
