# AGENTS.md

YouTube チャンネルを監視し、字幕 → AI 要約 → Discord Webhook 投稿する Python の cron バッチ。

## 必読（短い）

- 実行はホストの `.venv` + `PYTHONPATH=src`。要約の既定はホストの Codex CLI（`SUMMARY_PROVIDER=codex`）。
- コミットメッセージは日本語（`feature:` / `fix:` / `doc:` / `chore:` 等）。機能は `feature/<name>` → `develop` へ PR。
- `.env` や秘密情報はコミットしない。

## コマンド

```bash
source .venv/bin/activate
make test
make run                 # latest（字幕）
make run MODE=summarize  # 要約
PYTHONPATH=src python src/bot/main.py
```

cron 用: `src/script/get_summary_latest.sh`（latest→summarize）、`src/script/send_message.sh`。

## どこを読むか（必要なときだけ）

| 知りたいこと | 参照先 |
|---|---|
| セットアップ・使い方 | `README.md` |
| 環境変数一覧 | `.env.example` |
| 詳細仕様・落とし穴 | `document/project-spec.md` |
| フロー / ER / クラス | `document/` |
| DB 初期化・差分 | `sql/create.sql`, `sql/migrate_*.sql` |
| エントリ | `src/main.py`, `src/bot/main.py` |

作業前に、上表から関連するものだけ読んでから着手する。README や仕様の全文を毎回読まない。

## 変更時の注意（常に効くものだけ）

- Discord は 1 実行 1 動画。送信が全チャンク成功したときだけ `summary_send_flag` を更新する。
- 失敗通知は `NTFY_URL`（任意）。未設定なら通知しない。
- アプリ本体はDocker化せず、ホストのvenv＋cronで動かす。PostgreSQLのみ `deploy/postgres/` の専用コンテナを使う。
