# 動画要約のフロー図

## 動画メタデータ同期（sync）

```mermaid
graph TD
CronSync["Crontab run_pipeline_step.sh sync"] --> MainSync["main.py sync"]
MainSync --> YF["YoutubeFetcher.fetch_all_videos"]
YF --> API["YouTube Data API"]
MainSync --> IDs["DB video IDs"]
IDs --> Compare["ID差分"]
Compare -->|未登録のみ| Save["save_db_new_data"]
Save --> EndSync["終了"]
```

## 字幕取得（captions）

```mermaid
graph TD
CronCaptions["Crontab run_pipeline_step.sh captions"] --> MainCaptions["main.py captions"]
MainCaptions --> Rows["get_none_caption_record"]
Rows --> Cap["get_caption"]
Cap -->|成功| Prep["prepare_caption_for_storage"]
Prep --> SaveCap["save_caption_data"]
Cap -->|失敗| Mark["mark_caption_unavailable"]
SaveCap --> EndCaptions["終了"]
Mark --> EndCaptions
```

## 要約生成（summarize）

```mermaid
graph TD
Main["main.py summarize"] --> Rows["get_none_summary_record"]
Rows --> Sum["get_summary (codex/openai/lmstudio)"]
Sum --> Save["save_summary_data"]
Save --> End["終了"]
```

## チャンネル全動画（all）

```mermaid
graph TD
Main["main.py all"] --> YF["YoutubeFetcher.fetch_all_videos"]
YF --> Save["save_db_new_data"]
Save --> CapLoop["fetch_captions と同様に未取得字幕を処理"]
CapLoop --> End["終了"]
```

## Discord 投稿

```mermaid
graph TD
Cron["Crontab send_message.sh"] --> Bot["bot/main.py"]
Bot --> Get["get_not_send_summaries_data"]
Get --> Send["Webhook 送信（1件・分割）"]
Send --> Flag["update_summary_send_flag"]
Flag --> End["終了"]
```
