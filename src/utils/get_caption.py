import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_languages() -> list[str]:
    """CAPTION_LANGUAGES 環境変数からリストを構築する（デフォルト: ['ja']）"""
    raw = os.getenv("CAPTION_LANGUAGES", "ja")
    return [lang.strip() for lang in raw.split(",") if lang.strip()]


def get_caption(video_id: str, max_retries: int = 3):
    """対象のYouTube動画のIDを指定。字幕が取得できない場合は None を返す。"""
    languages = _get_languages()

    for attempt in range(max_retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            return " ".join([item["text"] for item in transcript])

        except (NoTranscriptFound, TranscriptsDisabled) as e:
            logger.warning(f"字幕なし (video_id={video_id}): {e}")
            return None

        except Exception as e:
            if attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                logger.warning(
                    f"字幕取得失敗 ({attempt + 1}/{max_retries}) (video_id={video_id}): {e} "
                    f"— {wait}秒後にリトライ"
                )
                time.sleep(wait)
            else:
                logger.error(f"字幕取得失敗 全試行終了 (video_id={video_id}): {e}")
                return None
