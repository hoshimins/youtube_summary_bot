-- 既存 DB 向けの差分適用（create.sql と揃える）
-- psql -U <user> -d <database> -f sql/migrate_2026_03_align_schema.sql

ALTER TABLE youtube_feed_summary.video
    ALTER COLUMN title TYPE TEXT;

ALTER TABLE youtube_feed_summary.captions
    ADD COLUMN IF NOT EXISTS caption_unavailable BOOLEAN NOT NULL DEFAULT FALSE;
