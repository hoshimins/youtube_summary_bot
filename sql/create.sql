-- スキーマの作成
CREATE SCHEMA IF NOT EXISTS youtube_feed_summary;

-- チャンネル情報保存テーブル
CREATE TABLE IF NOT EXISTS youtube_feed_summary.channel (
    channel_id VARCHAR(255) NOT NULL PRIMARY KEY,
    channel_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 動画情報保存テーブル
CREATE TABLE IF NOT EXISTS youtube_feed_summary.video (
    video_id VARCHAR(255) NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    channel_id VARCHAR(255) NOT NULL,
    published DATE NOT NULL,
    link VARCHAR(255),
    summary_send_flag BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (channel_id) REFERENCES youtube_feed_summary.channel (channel_id) ON DELETE CASCADE
);

-- 動画字幕情報保存テーブル
CREATE TABLE IF NOT EXISTS youtube_feed_summary.captions (
    video_id VARCHAR(255) NOT NULL PRIMARY KEY,
    caption TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES youtube_feed_summary.video (video_id) ON DELETE CASCADE
);

-- 要約情報保存テーブル
CREATE TABLE IF NOT EXISTS youtube_feed_summary.summary (
    video_id VARCHAR(255) NOT NULL PRIMARY KEY,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES youtube_feed_summary.video (video_id) ON DELETE CASCADE
);

-- DROP TABLE youtube_feed_summary.captions;
-- DROP TABLE youtube_feed_summary.summary;
-- DROP TABLE youtube_feed_summary.video;
-- DROP TABLE youtube_feed_summary.channel;
