# YouTube Summary Bot — プロジェクト仕様書

## プロジェクト概要

YouTube チャンネルの最新動画を監視し、字幕を取得して AI で要約を生成、Discord Webhook に自動投稿するシステム。cron で定期実行することを前提に設計されている。

要約のデフォルトプロバイダーは **Codex CLI**（自宅サーバーのホストにインストール済みの `codex` を呼び出し）。必要に応じて OpenAI API / LM Studio にも切り替え可能。

---

## アーキテクチャ

```
cron
 ├─ get_summary_latest.sh
 │    ├─ src/main.py latest     (RSS監視 → 字幕取得 → DB 保存)
 │    └─ src/main.py summarize  (字幕済み・未要約を Codex 等で要約)
 └─ send_message.sh → src/bot/main.py  (未送信要約を Discord に投稿・1実行1件)
```

### データフロー（main.py latest / all / id）

1. DB の `channel` テーブルからチャンネルIDを取得（`LIMIT 1`）
2. モードに応じて動画一覧を取得
   - `latest`: RSS
   - `all` / `id`: YouTube Data API v3
3. 新着を `video` / `captions` / `summary` に挿入（caption・summary は NULL）
4. `caption IS NULL` かつ `caption_unavailable = FALSE` を処理
   - `youtube-transcript-api` で字幕取得（`CAPTION_LANGUAGES`）
   - 長すぎる字幕は `CAPTION_MAX_CHARS` で切り詰めてから DB 保存
   - 取得不可は `caption_unavailable = TRUE`

### データフロー（main.py summarize）

1. `summary IS NULL` かつ `caption IS NOT NULL` のレコードを取得
2. `SUMMARY_PROVIDER` に応じて要約
   - `codex`（デフォルト）: 一時ファイルに字幕を書き、`codex exec` で要約
   - `openai` / `lmstudio`: OpenAI 互換 Chat Completions
3. 要約を `summary` テーブルへ保存

### データフロー（bot/main.py）

1. `summary_send_flag = false` かつ `summary IS NOT NULL` の最古 1 件を取得
2. Discord Webhook へ 1950 文字ずつ分割して送信（チャンク間 1 秒）
3. 送信完了後 `summary_send_flag = true` に更新

---

## ファイル構成

```
youtube_summary_bot/
├── src/
│   ├── main.py                      # latest|all|id|summarize
│   ├── classes/
│   │   ├── database_manager.py
│   │   ├── youtube_fetcher.py
│   │   └── youtube_summary_bot.py   # Discord Webhook 送信
│   ├── utils/
│   │   ├── config.py
│   │   ├── comparison_data.py
│   │   ├── fetch_rss_feed.py
│   │   ├── get_caption.py
│   │   ├── caption_text.py          # 字幕正規化・文字数制限
│   │   ├── get_summary.py           # Codex / OpenAI / LM Studio
│   │   └── logger.py
│   ├── bot/main.py
│   └── script/
│       ├── get_summary_latest.sh
│       ├── send_message.sh
│       ├── get_summary_latest.py
│       └── get_all_channel_video.py
├── sql/
│   ├── create.sql
│   └── migrate_2026_09_align_schema.sql
├── document/
├── Dockerfile                       # 主に字幕取得用（要約はホスト Codex 推奨）
├── Makefile
├── requirements.txt
└── .env
```

---

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL 接続文字列 |
| `YOUTUBE_API_KEY` | YouTube Data API v3（`all` / `id` で必要） |
| `SUMMARY_PROVIDER` | `codex`（既定）/ `openai` / `lmstudio` |
| `CODEX_BIN` | Codex 実行ファイル（既定: `codex`） |
| `CODEX_MODEL` | 任意。Codex の `-m` |
| `CODEX_TIMEOUT` | Codex タイムアウト秒（既定: 600） |
| `LM_STUDIO_BASE_URL` / `LM_STUDIO_MODEL` | LM Studio 用 |
| `OPENAI_API_KEY` | `SUMMARY_PROVIDER=openai` 用 |
| `WEBHOOK_URL` | Discord Webhook URL |
| `SUMMARY_TEXT_CHANNEL_ID` | 現状 Webhook では未使用 |
| `CAPTION_LANGUAGES` | 字幕言語優先順（既定: `en`） |
| `CAPTION_SLEEP_INTERVAL` | 字幕取得間隔秒（既定: 30） |
| `CAPTION_MAX_CHARS` | DB/要約前の字幕最大文字数（既定: 100000） |

---

## 実行方法

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

psql -U <user> -d <database> -f sql/create.sql
# 既存 DB なら
psql -U <user> -d <database> -f sql/migrate_2026_09_align_schema.sql

# Step 1: 字幕
PYTHONPATH=src python src/main.py latest

# Step 2: 要約（ホストに Codex ログイン済みであること）
PYTHONPATH=src python src/main.py summarize

# Step 3: Discord
PYTHONPATH=src python src/bot/main.py
```

---

## DB スキーマ概要

スキーマ名: `youtube_feed_summary`

| テーブル | 主キー | 説明 |
|---------|--------|------|
| `channel` | `channel_id` | 監視対象。現状 1 件想定 |
| `video` | `video_id` | `summary_send_flag` で Discord 送信管理。`title` は TEXT |
| `captions` | `video_id` | 字幕。`caption_unavailable` で取得不可を記録 |
| `summary` | `video_id` | 要約。NULL = 未生成 |

---

## 開発規約

### コミットメッセージ

日本語。プレフィックス例: `feature:` / `fix:` / `doc:` / `modify:` / `chore:`

### ブランチ戦略

- `main` — リリース済み
- `develop` — 開発統合
- `release` — リリース用
- 機能は `feature/<name>` から develop へ PR

---

## 既知の制限事項・注意点

- 指定言語の字幕がない動画は `caption_unavailable` になりスキップされる
- チャンネルは `LIMIT 1`（マルチチャンネル未対応）
- `all` モードは YouTube API クォータを大量消費する
- Discord は **1 実行につき 1 動画**（レート制限対策）
- Codex 要約はホストの `codex` と認証が必要。Docker 内からの利用は想定外
- 長い字幕は `CAPTION_MAX_CHARS` で切り詰められる

---

## よくある落とし穴

| 症状 | 原因 | 対処 |
|------|------|------|
| `module not found: utils` | `PYTHONPATH` 未設定 | `export PYTHONPATH=src` |
| `channelテーブルにデータが存在しません` | channel が空 | 手動 INSERT |
| Codex が見つからない | PATH / `CODEX_BIN` | ホストで `which codex` |
| 字幕取得で繰り返し失敗 | 字幕なし | `caption_unavailable` を確認 |
| Discord に出ない | 未要約 or 送信済み | `summary` と `summary_send_flag` を確認 |
