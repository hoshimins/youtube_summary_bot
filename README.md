# YouTube Summary Bot

YouTube動画の字幕を自動取得し、AI（OpenAI GPT-4o）で要約を生成してDiscordに投稿する自動化Botシステムです。

## 概要

このBotは以下の処理を自動化します：
1. YouTubeチャンネルのRSSフィードから最新動画を監視
2. 動画の日本語字幕を自動取得
3. OpenAI GPT-4oで字幕を要約
4. 生成した要約をDiscord Webhookで投稿

cronによる定期実行で、常に最新動画の要約をDiscordに自動投稿できます。

## 主要機能

### 🎥 動画情報の取得
- RSSフィードからの最新動画取得
- YouTube Data API v3による全動画一括取得
- 個別動画IDからの情報取得

### 📝 字幕の自動取得
- `youtube-transcript-api`による日本語字幕の取得
- 自動生成字幕にも対応
- 字幕データのデータベース保存

### 🤖 AI要約生成
- OpenAI GPT-4oによる高品質な要約
- 構造化された要約フォーマット：
  - タイトル
  - はじめに（動機・背景）
  - 主なメッセージと重要なアドバイス（約5000文字）
  - おわりに

### 💬 Discord投稿
- Webhook経由での自動投稿
- 長文の自動分割送信（最大1950文字/メッセージ）
- 重複投稿防止（送信済みフラグ管理）

## システム要件

- Python 3.8以上
- PostgreSQL
- YouTube Data API v3のAPIキー
- OpenAI APIキー
- Discord Webhook URL

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd youtube_summary_bot
```

### 2. 仮想環境の作成と有効化

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. データベースのセットアップ

PostgreSQLにデータベースとスキーマを作成します：

```bash
psql -U your_user -d your_database -f sql/create.sql
```

### 5. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定します：

```bash
# データベース接続
DATABASE_URL=postgresql://user:password@host:port/database

# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Discord Webhook
WEBHOOK_URL=your_discord_webhook_url
SUMMARY_TEXT_CHANNEL_ID=your_channel_id
```

## 使い方

### 最新動画の要約生成

```bash
# シェルスクリプト経由
./src/script/get_summary_latest.sh

# または直接実行
python src/main.py latest
```

### 全動画の一括取得

```bash
python src/main.py all
```

### 特定動画IDの処理

```bash
python src/main.py id VIDEO_ID
```

### Discord投稿

```bash
# シェルスクリプト経由
./src/script/send_message.sh

# または直接実行
python src/bot/main.py
```

### Makefileの使用

```bash
# デフォルト（latest）
make run

# モード指定
make run MODE=all
```

## Cron設定

定期実行を設定する場合、以下のようにcrontabに追加します：

```cron
# 最新動画の要約生成（毎時0分）
0 * * * * /path/to/youtube_summary_bot/src/script/get_summary_latest.sh >> /path/to/youtube_summary_bot/summary.log 2>&1

# Discord投稿（毎時30分）
30 * * * * /path/to/youtube_summary_bot/src/script/send_message.sh >> /path/to/youtube_summary_bot/send.log 2>&1
```

## プロジェクト構造

```
youtube_summary_bot/
├── src/
│   ├── main.py                    # メインスクリプト
│   ├── classes/
│   │   ├── database_manager.py    # データベース操作
│   │   ├── youtube_fetcher.py     # YouTube API操作
│   │   └── youtube_summary_bot.py # Discord投稿
│   ├── utils/
│   │   ├── config.py             # 環境変数管理
│   │   ├── comparison_data.py    # データ比較
│   │   ├── fetch_rss_feed.py     # RSSフィード取得
│   │   ├── get_caption.py        # 字幕取得
│   │   └── get_summary.py        # 要約生成
│   ├── script/
│   │   ├── get_summary_latest.sh
│   │   ├── get_summary_latest.py
│   │   ├── get_all_channel_video.py
│   │   └── send_message.sh
│   └── bot/
│       └── main.py               # Discord投稿メイン
├── sql/
│   └── create.sql                # DBスキーマ定義
├── document/                      # 各種設計書
├── requirements.txt
├── Makefile
└── .env
```

## データベーススキーマ

スキーマ名: `youtube_feed_summary`

### channel テーブル
チャンネル情報を管理

| カラム名 | 型 | 説明 |
|---------|---|------|
| channel_id | VARCHAR(255) | チャンネルID（主キー）|
| channel_name | VARCHAR(255) | チャンネル名 |
| created_at | TIMESTAMP | 作成日時 |

### video テーブル
動画情報を管理

| カラム名 | 型 | 説明 |
|---------|---|------|
| video_id | VARCHAR(255) | 動画ID（主キー）|
| title | VARCHAR(255) | 動画タイトル |
| channel_id | VARCHAR(255) | チャンネルID（外部キー）|
| published | DATE | 公開日 |
| link | VARCHAR(255) | 動画URL |
| summary_send_flag | BOOLEAN | 送信済みフラグ |

### captions テーブル
字幕データを保存

| カラム名 | 型 | 説明 |
|---------|---|------|
| video_id | VARCHAR(255) | 動画ID（主キー、外部キー）|
| caption | TEXT | 字幕テキスト |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

### summary テーブル
要約データを保存

| カラム名 | 型 | 説明 |
|---------|---|------|
| video_id | VARCHAR(255) | 動画ID（主キー、外部キー）|
| summary | TEXT | 要約テキスト |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

## 技術スタック

### 主要ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|----------|------|
| discord.py | 2.5.2 | Discord API連携 |
| feedparser | 6.0.11 | RSSフィード解析 |
| google-api-python-client | 2.165.0 | YouTube Data API |
| openai | latest | OpenAI API連携 |
| psycopg2-binary | 2.9.10 | PostgreSQL接続 |
| python-dotenv | 1.0.1 | 環境変数管理 |
| requests | 2.32.3 | HTTP通信 |
| youtube-transcript-api | 1.0.2 | YouTube字幕取得 |

## システムアーキテクチャ

```
┌─────────────┐
│  Crontab    │ ← 定期実行トリガー
└──────┬──────┘
       │
       ├─► get_summary_latest (最新動画の要約)
       ├─► get_all_channel_video (全動画取得)
       └─► send_message (Discord投稿)
              │
              ▼
       ┌─────────────────┐
       │   Main Script    │
       └─────────┬────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│RSSFeed   │ │Caption   │ │Summary   │
│Fetcher   │ │Fetcher   │ │Generator │
└──────────┘ └──────────┘ └──────────┘
      │          │          │
      └──────────┴──────────┘
                 │
                 ▼
       ┌──────────────────┐
       │ DatabaseManager  │
       └─────────┬────────┘
                 │
                 ▼
          ┌──────────┐
          │PostgreSQL│
          └──────────┘
```

## 処理フロー

### 最新動画の要約生成フロー

1. データベースから最新情報を取得
2. RSSフィードから最新動画情報を取得
3. データベースと比較して新着動画を検出
4. 新着動画があれば：
   - データベースに動画情報を保存
   - 字幕を取得してデータベースに保存
   - OpenAI APIで要約を生成
   - 要約をデータベースに保存

### Discord投稿フロー

1. データベースから未送信の要約を取得
2. 要約があれば：
   - タイトルとURLをDiscordに送信
   - 本文を1950文字ずつ分割して送信
   - 送信済みフラグを更新

## 注意事項

### API制限
- **YouTube Data API**: 1日あたりのクォータ制限があります
- **OpenAI API**: 使用量に応じた課金が発生します

### 字幕取得
- 日本語字幕が存在しない動画は処理できません
- 自動生成字幕も取得可能です

### パフォーマンス
- 全動画取得（`all`モード）は大量のAPIコールを実行するため注意が必要です
- ページネーション対応済み（最大50件/リクエスト）

### エラーハンドリング
- データベース接続エラー時は自動でロールバックされます
- API呼び出しエラーは個別にログに記録されます

## 今後の拡張案

- マルチチャンネル対応
- Discord Bot化（Webhook → Bot化）
- 要約言語の多言語対応
- 要約モデルの選択可能化
- ログ管理の改善
- エラー通知機能の追加

## ドキュメント

詳細な仕様やアーキテクチャについては、以下のドキュメントを参照してください：

- [CLAUDE.md](./CLAUDE.md) - プロジェクト仕様書
- [document/architecture.md](./document/architecture.md) - アーキテクチャ図
- [document/flowchart.md](./document/flowchart.md) - フローチャート
- [document/er.md](./document/er.md) - ER図
- [document/class.md](./document/class.md) - クラス図

## ライセンス

このプロジェクトのライセンスについては、プロジェクトオーナーに確認してください。
