# YouTube Summary Bot — 詳細仕様（参照用）

エージェント向けの要約はリポジトリ直下の `AGENTS.md` を見る。ここでは詳細のみ載せる。

## プロジェクト概要

YouTube チャンネルの最新動画を監視し、字幕を取得して AI で要約を生成、Discord Webhook に自動投稿するシステム。cron で定期実行することを前提に設計されている。

要約のデフォルトプロバイダーは **Codex CLI**（自宅サーバーのホストにインストール済みの `codex` を呼び出し）。必要に応じて OpenAI API / LM Studio にも切り替え可能。

---

## アーキテクチャ

```
cron
 ├─ run_pipeline_step.sh sync      → src/main.py sync       (動画メタデータ同期)
 ├─ run_pipeline_step.sh captions  → src/main.py captions   (字幕取得)
 ├─ run_pipeline_step.sh summarize → src/main.py summarize  (要約生成)
 └─ send_message.sh → src/bot/main.py                    (未送信要約をDiscordへ投稿・1実行1件)
```

### データフロー（main.py sync）

1. DB の `channel` テーブルからチャンネルIDを取得（複数チャンネルを順次）
2. YouTube Data API v3 の uploads playlist から公開動画を取得
3. DBにない動画だけを `video` / `captions` / `summary` に挿入（caption・summary は NULL）

### データフロー（main.py captions）

1. DBに登録済みで `caption IS NULL` かつ `caption_unavailable = FALSE` の動画を取得
2. `youtube-transcript-api` で字幕取得（`CAPTION_LANGUAGES`）
3. 長すぎる字幕は `CAPTION_MAX_CHARS` で切り詰めてDB保存
4. 取得不可は `caption_unavailable = TRUE`

`id` モードは従来互換として、指定動画のメタデータを登録した後、未取得字幕を処理する。

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
│   ├── main.py                      # sync|captions|latest|all|id|summarize
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
│       ├── run_pipeline_step.sh
│       ├── send_message.sh
│       ├── get_summary_latest.py
│       └── get_all_channel_video.py
├── sql/
│   ├── create.sql
│   └── migrate_2026_09_align_schema.sql
├── document/
├── Makefile
├── requirements.txt
└── .env
```

---

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL 接続文字列 |
| `YOUTUBE_API_KEY` | YouTube Data API v3（`sync` / `all` / `audit` / `id` / チャンネル名自動取得で必要） |
| `SUMMARY_PROVIDER` | `codex`（既定）/ `openai` / `lmstudio` |
| `CODEX_BIN` | Codex 実行ファイル（既定: `codex`） |
| `CODEX_MODEL` | 任意。Codex の `-m` |
| `CODEX_TIMEOUT` | Codex タイムアウト秒（既定: 600） |
| `SUMMARIZE_BATCH_LIMIT` | 1 回の summarize 最大件数（既定: 3、0 で無制限） |
| `LM_STUDIO_BASE_URL` / `LM_STUDIO_MODEL` | LM Studio 用 |
| `OPENAI_API_KEY` | `SUMMARY_PROVIDER=openai` 用 |
| `WEBHOOK_URL` | Discord Webhook URL |
| `SUMMARY_TEXT_CHANNEL_ID` | 現状 Webhook では未使用 |
| `CAPTION_LANGUAGES` | 字幕言語優先順（既定: `en`） |
| `CAPTION_SLEEP_INTERVAL` | 字幕取得間隔秒（既定: 30） |
| `CAPTION_MAX_CHARS` | DB/要約前の字幕最大文字数（既定: 100000） |
| `NTFY_URL` | 失敗通知用 ntfy トピック URL（未設定なら通知しない） |
| `NTFY_TOKEN` | ntfy Bearer トークン（任意） |

---

## 実行方法

```bash
make setup
# 依存関係を同期し直す場合
make sync

psql -U <user> -d <database> -f sql/create.sql
# 既存 DB なら
psql -U <user> -d <database> -f sql/migrate_2026_09_align_schema.sql

# Step 1: 動画メタデータ同期
make sync-videos

# Step 2: 字幕
make captions

# Step 3: 要約（ホストに Codex ログイン済みであること）
PYTHONPATH=src .venv/bin/python src/main.py summarize

# Step 4: Discord
PYTHONPATH=src .venv/bin/python src/bot/main.py
```

### 監査・チャンネル管理

監査は DB を変更せず、登録済みチャンネルごとに YouTube と DB の動画IDを比較する。

```bash
make audit
make audit AUDIT_LIMIT=50
make audit AUDIT_SOURCE=rss
make audit AUDIT_FORMAT=json

make channel-list
PYTHONPATH=src .venv/bin/python src/script/manage_channels.py add UC... "チャンネル名"
```

API 全件監査では、YouTubeにありDBにない未取得候補、DBにあるがYouTubeから確認できない動画、字幕・要約・Discord送信の処理状況を出力する。RSS は最新フィードだけの限定比較で、公開動画総数は取得できない。

同期と要約は分離されている。`sync-videos` は動画メタデータだけをDBへ登録し、`captions` は字幕だけ、`summarize` は要約だけを処理する。

## DB スキーマ概要

スキーマ名: `youtube_feed_summary`

| テーブル | 主キー | 説明 |
|---------|--------|------|
| `channel` | `channel_id` | 監視対象チャンネル（複数可） |
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
- チャンネルは複数登録可。`sync` / 互換モードの `latest`・`all` は全チャンネルを順に処理する
- `sync` は YouTube API の uploads playlist を全件確認するため、チャンネル数に応じて API クォータを消費する
- Discord は **1 実行につき 1 動画**。送信が全チャンク成功したときだけ `summary_send_flag` を更新
- `summarize` は `SUMMARIZE_BATCH_LIMIT`（既定 3）件まで
- Codex 要約はホストの `codex` と認証が必要
- 長い字幕は `CAPTION_MAX_CHARS` で切り詰められる
- 字幕取得は `CAPTION_SLEEP_INTERVAL` の待機を挟むため、未処理件数が多い場合は複数回のcron実行にまたがる
- 既存 DB は `sql/migrate_2026_09_align_schema.sql` の適用が必要な場合がある

---

## よくある落とし穴

| 症状 | 原因 | 対処 |
|------|------|------|
| `module not found: utils` | `PYTHONPATH` 未設定 | `export PYTHONPATH=src` |
| `channelテーブルにデータが存在しません` | channel が空 | 手動 INSERT |
| Codex が見つからない | PATH / `CODEX_BIN` | ホストで `which codex` |
| `caption_unavailable` カラムがない | マイグレーション未適用 | `migrate_2026_09_align_schema.sql` |
| 字幕取得で繰り返し失敗 | 字幕なし | `caption_unavailable` を確認 |
| Discord に出ない | 未要約 / 送信失敗 / 送信済み | `summary` と `summary_send_flag` を確認 |
