# YouTube Summary Bot — プロジェクト仕様書

## プロジェクト概要

YouTube チャンネルの最新動画を監視し、日本語字幕を取得して OpenAI GPT-4o で要約を生成、Discord Webhook に自動投稿するシステム。cron で定期実行することを前提に設計されている。

---

## アーキテクチャ

```
cron
 ├─ get_summary_latest.sh  →  src/main.py latest  (RSS監視 → 字幕取得 → 要約生成)
 └─ send_message.sh        →  src/bot/main.py      (未送信要約を Discord に投稿)
```

### データフロー（main.py latest）

1. DB の `channel` テーブルからチャンネルIDを取得
2. RSS フィードから最新動画一覧を取得 (`fetch_rss_feed`)
3. DB の動画一覧と比較して新着を検出 (`comparison_data`)
4. 新着動画を `video` / `captions` / `summary` テーブルに挿入（caption・summary は NULL）
5. `captions.caption IS NULL` のレコードを全件処理：
   - `youtube-transcript-api` で日本語字幕を取得
   - OpenAI GPT-4o で要約を生成
   - DB に保存

### データフロー（bot/main.py）

1. `summary_send_flag = false` かつ `summary IS NOT NULL` の動画を取得
2. Discord Webhook へ 1950 文字ずつ分割して送信
3. 送信完了後 `summary_send_flag = true` に更新

---

## ファイル構成

```
youtube_summary_bot/
├── src/
│   ├── main.py                      # エントリポイント。mode=latest|all|<video_id>
│   ├── classes/
│   │   ├── database_manager.py      # 全 DB 操作（psycopg2）
│   │   ├── youtube_fetcher.py       # YouTube Data API v3 ラッパー
│   │   └── youtube_summary_bot.py   # Discord Webhook 送信
│   ├── utils/
│   │   ├── config.py                # .env 読み込み（1度だけ）
│   │   ├── comparison_data.py       # RSS取得データと DB データの差分比較
│   │   ├── fetch_rss_feed.py        # RSS フィード取得・パース
│   │   ├── get_caption.py           # youtube-transcript-api ラッパー
│   │   └── get_summary.py           # OpenAI GPT-4o 要約生成
│   ├── bot/
│   │   └── main.py                  # Discord 投稿エントリポイント
│   └── script/
│       ├── get_summary_latest.sh    # cron 用ラッパー（要約生成）
│       ├── send_message.sh          # cron 用ラッパー（Discord 投稿）
│       ├── get_summary_latest.py    # スクリプト経由の要約実行
│       └── get_all_channel_video.py # チャンネル全動画の一括取得スクリプト
├── sql/
│   └── create.sql                   # DB スキーマ定義（初回セットアップ用）
├── document/                        # 設計書（architecture/flowchart/er/class）
├── Makefile
├── requirements.txt
└── .env                             # 環境変数（git 管理外）
```

---

## 環境変数

`.env` ファイルに以下を設定する。

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL 接続文字列（例: `postgresql://user:pass@host:5432/dbname`）|
| `YOUTUBE_API_KEY` | YouTube Data API v3 のキー |
| `OPENAI_API_KEY` | OpenAI API キー |
| `WEBHOOK_URL` | Discord Webhook URL |
| `SUMMARY_TEXT_CHANNEL_ID` | Discord チャンネル ID（現状未使用、将来のBot化に備えて保持）|

---

## 実行方法

```bash
# 仮想環境セットアップ（初回）
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# DB スキーマ作成（初回）
psql -U <user> -d <database> -f sql/create.sql

# 最新動画の要約生成
PYTHONPATH=src python src/main.py latest

# 全動画一括取得（DB に channel が登録済みであること）
PYTHONPATH=src python src/main.py all

# 特定動画IDで処理
PYTHONPATH=src python src/main.py id <VIDEO_ID>

# Discord に未送信の要約を投稿
PYTHONPATH=src python src/bot/main.py

# Makefile 経由（latest がデフォルト）
make run
make run MODE=all
```

---

## DB スキーマ概要

スキーマ名: `youtube_feed_summary`

| テーブル | 主キー | 説明 |
|---------|--------|------|
| `channel` | `channel_id` | 監視対象チャンネル。現状1件のみ想定 |
| `video` | `video_id` | 動画情報。`summary_send_flag` で Discord 送信済みを管理 |
| `captions` | `video_id` | 字幕テキスト。NULL = 未取得 |
| `summary` | `video_id` | 要約テキスト。NULL = 未生成 |

`channel` → `video` → `captions` / `summary` の順で CASCADE DELETE が設定されている。

---

## 開発規約

### コミットメッセージ

日本語で記述。プレフィックス例:

```
feature: <新機能>
fix: <バグ修正>
doc: <ドキュメント更新>
modify: <既存機能の変更>
chore: <雑務・設定変更>
```

### ブランチ戦略

- `main` — リリース済みコード
- `develop` — 開発中コード（PR のマージ先）
- `release` — リリース用
- 機能開発は `feature/<name>` ブランチを切って develop に PR を出す

---

## 既知の制限事項・注意点

- **日本語字幕がない動画はスキップされる**。字幕取得失敗時は `captions.caption` が NULL のまま残る。
- **`channel` テーブルには1件だけ登録を想定**。`get_channel_data()` は `LIMIT 1` で取得している。マルチチャンネル対応は未実装。
- **`all` モードは YouTube Data API のクォータを大量消費する**。日次クォータ（10,000ユニット/日）に注意。
- **`discord.py` は現在 Webhook 送信のみ使用**。`YoutubeSummaryBot` は `discord.Client` を継承しているが Bot 機能は未使用。
- **cron 実行時は `PYTHONPATH` の設定が必要**。`send_message.sh` 内で `$PROJECT_ROOT/src` をセットしている。
- **OpenAI API の要約生成は字幕が長いほど時間・コストがかかる**。タイムアウト設定なし。

---

## よくある落とし穴

| 症状 | 原因 | 対処 |
|------|------|------|
| `module not found: utils` | `PYTHONPATH=src` が未設定 | `export PYTHONPATH=src` してから実行 |
| `channelテーブルにデータが存在しません` | DB の `channel` テーブルが空 | `all` モードや `id` モードの前に channel を手動 INSERT |
| 字幕取得で無限に失敗 | 対象動画に日本語字幕がない | `get_caption` は `None` を返してスキップするため、`captions` テーブルに NULL レコードが残る。手動でダミー値を UPDATE するか動画をスキップ |
| Discord に投稿されない | `summary_send_flag` の更新漏れ or `summary IS NULL` | DB を直接確認して `summary_send_flag` と `summary` の状態を確認 |
