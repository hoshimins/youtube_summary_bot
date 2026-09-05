# youtube_summary_bot 用 PostgreSQL

このComposeプロジェクトは、youtube_summary_bot専用のPostgreSQLだけを起動します。
アプリ本体は自宅サーバーのホスト上のPython venvとcronで動かし、既存のSolidtime・Paperless-ngxのPostgreSQLコンテナには相乗りさせません。

移行元SupabaseがPostgreSQL 17.6のため、移行先も `postgres:17` を使用します。既存のSolidtime・Paperless-ngx用PostgreSQL 15コンテナは変更しません。

## 既存コンテナと分離する理由

自宅サーバーにはSolidtimeとPaperless-ngxがそれぞれ専用のPostgreSQLコンテナ、ネットワーク、データ領域を持っています。
それらへyoutube_summary_botのDBを追加すると、次のライフサイクルが結合します。

- 既存アプリのCompose更新・停止が、ボットDBに影響する
- 既存アプリ用バックアップにボットDBが混ざり、復旧単位が不明確になる
- DBユーザー・拡張・バージョン変更の影響範囲が広がる

専用コンテナなら、ボット用DBの停止・バックアップ・復元・PostgreSQL更新を独立して扱えます。
ホスト側からだけ接続できるよう、ポートはデフォルトで `127.0.0.1:5433` に公開します。

## 初回セットアップ

```bash
cd /path/to/youtube_summary_bot/deploy/postgres
cp .env.example .env
openssl rand -hex 32
# 生成した値を .env の POSTGRES_PASSWORD に設定する
chmod 600 .env

docker compose --env-file .env -f compose.yml config
docker compose --env-file .env -f compose.yml up -d
docker compose --env-file .env -f compose.yml ps
```

`POSTGRES_DATA_DIR` はDocker管理外の永続領域です。初回起動時にディレクトリが作成されます。
`.env` はGit管理対象外です。

## Supabaseからの移行

移行前に、現在のリポジトリの `.env` にある `DATABASE_URL` が移行元を指していることを確認します。
Supabase全体ではなく、ボットが使用する `youtube_feed_summary` スキーマだけをダンプします。
ダンプはデータ領域にバックアップとして保存し、復元確認が終わるまで削除しません。

```bash
cd /path/to/youtube_summary_bot
mkdir -p /export/data/youtube-summary-postgres/backups
dump=/export/data/youtube-summary-postgres/backups/youtube_summary_$(date +%Y%m%d%H%M%S).dump

docker run --rm --env-file .env --entrypoint sh postgres:17 \
  -c 'pg_dump "$DATABASE_URL" --schema=youtube_feed_summary --format=custom --no-owner --no-acl' > "$dump"

cd deploy/postgres
docker compose --env-file .env -f compose.yml up -d
docker compose --env-file .env -f compose.yml exec -T db \
  sh -c 'export PGPASSWORD="$POSTGRES_PASSWORD"; pg_restore --exit-on-error --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$dump"
```

復元後、件数とスキーマを確認します。

```bash
docker compose --env-file .env -f compose.yml exec -T db \
  sh -c 'export PGPASSWORD="$POSTGRES_PASSWORD"; psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT table_name FROM information_schema.tables WHERE table_schema = '\''youtube_feed_summary'\'' ORDER BY table_name"'
```

アプリの `.env` の `DATABASE_URL` を次の形式に変更します。生成したパスワードはURLエンコードが不要な英数字のランダム値を使ってください。

```dotenv
DATABASE_URL=postgresql://youtube_summary:<password>@127.0.0.1:5433/youtube_summary
```

その後、アプリ側から接続確認とローカルテストを実行します。

```bash
cd /path/to/youtube_summary_bot
make test
PYTHONPATH=src python src/main.py summarize
```

移行元を停止・削除する前に、チャンネル数・動画数・字幕数・要約数、および実際のcron実行を確認してください。
