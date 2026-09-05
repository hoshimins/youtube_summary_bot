# YouTube Summary Bot

YouTube 動画の字幕を自動取得し、AI（デフォルト: Codex CLI）で要約して Discord に投稿する自動化 Bot です。

## 概要

1. YouTube Data API から動画メタデータを同期
2. 字幕を取得して PostgreSQL に保存（長文は文字数制限で切り詰め）
3. ホスト上の Codex CLI（または OpenAI / LM Studio）で要約
4. Discord Webhook で投稿（1 実行 1 件）

## 主要機能

- YouTube Data API による動画メタデータ同期
- `youtube-transcript-api` による字幕取得（言語は `CAPTION_LANGUAGES`）
- 字幕取得不可フラグ（`caption_unavailable`）
- 要約プロバイダー切替: `codex` / `openai` / `lmstudio`
- Discord Webhook 分割送信とレート制限対策

## システム要件

- mise
- uv（miseでリポジトリ単位に固定）
- Python 3.12.14（miseでリポジトリ単位に固定）
- PostgreSQL
- YouTube Data API v3 キー（`sync` / `all` / `audit` / `id` / チャンネル名自動取得時）
- **要約用**: ホストにインストール済みの Codex CLI（推奨）または OpenAI / LM Studio
- Discord Webhook URL

> 開発は MacBook、本番定期実行は自宅サーバー上の Codex を想定しています。GPU 付き Windows 上の LM Studio は任意のフォールバックです。

## セットアップ

```bash
git clone <repository-url>
cd youtube_summary_bot

make setup
# 依存関係を同期し直す場合
make sync

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
make setup  # 初回のみ
```

### Step 1: 動画メタデータ同期

DBとYouTubeの公開動画を揃える処理です。動画の登録だけを行い、字幕や要約は作りません。

```bash
make sync-videos
# 直接実行する場合
PYTHONPATH=src .venv/bin/python src/main.py sync
```

### Step 2: 字幕取得

DBに登録済みで字幕未取得の動画だけを処理します。

```bash
make captions
# 直接実行する場合
PYTHONPATH=src .venv/bin/python src/main.py captions
```

個別動画の登録・字幕取得（従来互換）:

```bash
PYTHONPATH=src .venv/bin/python src/main.py id VIDEO_ID
```

### Step 3: 要約生成（Codex 利用時はホストで実行）

```bash
PYTHONPATH=src .venv/bin/python src/main.py summarize
```

### Step 4: Discord 送信

```bash
PYTHONPATH=src .venv/bin/python src/bot/main.py
```

### シェルスクリプト（Step 1〜3）

```bash
./src/script/get_summary_latest.sh
./src/script/send_message.sh
```

cronでは `run_pipeline_step.sh` を使って、動画同期・字幕取得・要約を個別ジョブとして実行します。`get_summary_latest.sh` は手動で一括実行する場合の互換ラッパーです。

## データ監査とチャンネル管理

cron を再開する前に、YouTube 側の動画と DB の差分を読み取り専用で確認できます。

```bash
# YouTube Data API でアップロード一覧を全件取得して比較（推奨）
make audit

# API キーがない場合の簡易確認。RSS の最新フィード（通常は最新15件）のみ
make audit AUDIT_SOURCE=rss

# API quota を抑えて最新50件だけ比較
make audit AUDIT_LIMIT=50

# JSON で保存・加工したい場合
make audit AUDIT_FORMAT=json
```

API 全件監査では、未取得候補（YouTube に存在するが DB にない動画）と、DB にあるが YouTube から確認できない動画を分けて表示します。AUDIT_LIMIT を指定した場合、比較範囲外の古い DB 動画は削除扱いにしません。RSS は通知購読用の仕様として残っていますが、通常の一覧ポーリングには使わず、監査の診断用に限定しています。

監視チャンネルは DB に明示的に登録できます。add は同じチャンネル ID なら表示名を更新するだけで、動画データを削除しません。

```bash
make channel-list

# 表示名を指定して登録（API キー不要）
PYTHONPATH=src .venv/bin/python src/script/manage_channels.py add UCxxxxxxxxxxxxxxxxxxxxxx "チャンネル名"

# 表示名を省略すると YouTube Data API から取得
PYTHONPATH=src .venv/bin/python src/script/manage_channels.py add UCxxxxxxxxxxxxxxxxxxxxxx
```

## Cron 設定例

```cron
# 毎時、各段階を10分ずつずらして実行。flockで重複起動を防止。
0 * * * * /usr/bin/flock -n /tmp/youtube-summary-sync.lock /path/to/youtube_summary_bot/src/script/run_pipeline_step.sh sync >> /path/to/youtube_summary_bot/logs/sync.log 2>&1
10 * * * * /usr/bin/flock -n /tmp/youtube-summary-captions.lock /path/to/youtube_summary_bot/src/script/run_pipeline_step.sh captions >> /path/to/youtube_summary_bot/logs/captions.log 2>&1
20 * * * * /usr/bin/flock -n /tmp/youtube-summary-summarize.lock /path/to/youtube_summary_bot/src/script/run_pipeline_step.sh summarize >> /path/to/youtube_summary_bot/logs/summarize.log 2>&1
30 * * * * /usr/bin/flock -n /tmp/youtube-summary-send.lock /path/to/youtube_summary_bot/src/script/send_message.sh >> /path/to/youtube_summary_bot/logs/send.log 2>&1
```

本番の定期実行はホスト上の mise/uv 管理 `.venv` + `src/script/*.sh` + cron を想定しています（Codex CLI もホスト実行）。

## 自宅サーバーの PostgreSQL

本番ではアプリ本体をホストの venv + cron で実行し、PostgreSQLだけを専用コンテナで動かします。
既存のSolidtime・Paperless-ngx用PostgreSQLには相乗りさせず、`deploy/postgres/` のComposeプロジェクト、専用ネットワーク、専用永続領域で分離します。

```bash
cd deploy/postgres
cp .env.example .env
# .env の POSTGRES_PASSWORD を設定
docker compose --env-file .env -f compose.yml up -d
```

既存のSupabase DBから移行する場合のdump/restore手順は [`deploy/postgres/README.md`](deploy/postgres/README.md) を参照してください。


## 技術スタック

| ライブラリ | 用途 |
|-----------|------|
| requests | Discord Webhook HTTP 送信 |
| feedparser | RSS診断用 |
| google-api-python-client | YouTube Data API |
| openai | OpenAI / LM Studio 互換 API |
| psycopg2-binary | PostgreSQL |
| youtube-transcript-api | 字幕取得 |
| Codex CLI（外部） | デフォルトの要約エンジン |

## 処理フロー

1. `sync`: YouTube公開動画のメタデータをDBへ同期
2. `captions`: DB登録済み動画の字幕を取得
3. `summarize`: 字幕済み・未要約を Codex 等で生成
4. `bot/main.py`: 未送信 1 件を Discord へ

詳細は [AGENTS.md](./AGENTS.md)（エージェント向け要約）と [document/project-spec.md](./document/project-spec.md)、`document/` を参照。

## 注意事項

- 長い字幕は `CAPTION_MAX_CHARS` で切り詰めます（DB 保存失敗やコンテキスト超過の緩和）
- 字幕言語が無い動画はスキップされ、`caption_unavailable` が立ちます
- Discord はレート制限対策で 1 実行 1 動画です。送信失敗時はフラグを更新しません
- `summarize` は `SUMMARIZE_BATCH_LIMIT`（既定 3）件までに制限されます
- `channel` は複数登録可能。`sync` / 互換モードの `latest`・`all` は全チャンネルを順に処理します

## Makefile

```bash
make sync-videos      # 動画メタデータだけ同期
make captions         # 字幕だけ取得
make run MODE=summarize
make test             # ローカル単体テスト（GitHub Actions なし）
```

## 今後の拡張案

- 監査結果の通知・定期レポート
- Discord Bot 化
- 要約プロバイダーの自動フェイルオーバー
- 失敗時の ntfy 等通知

## ライセンス

プロジェクトオーナーに確認してください。
