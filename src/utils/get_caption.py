import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    IpBlocked,
    RequestBlocked,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# リトライ不要なエラー（字幕なし・IP ブロック等）
_NO_TRANSCRIPT_ERRORS = (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable)
_BLOCKED_ERRORS = (IpBlocked, RequestBlocked)


def _get_languages() -> list[str]:
    """CAPTION_LANGUAGES 環境変数からリストを構築する（デフォルト: ['en']）"""
    raw = os.getenv("CAPTION_LANGUAGES", "en")
    return [lang.strip() for lang in raw.split(",") if lang.strip()]


def get_caption(video_id: str, max_retries: int = 3):
    """対象のYouTube動画のIDを指定。字幕が取得できない場合は None を返す。"""
    languages = _get_languages()
    api = YouTubeTranscriptApi()

    for attempt in range(max_retries):
        try:
            transcript = api.fetch(video_id, languages=languages)
            return " ".join([item.text for item in transcript])

        except _NO_TRANSCRIPT_ERRORS as e:
            logger.warning(f"字幕なし (video_id={video_id}): {e}")
            return None

        except _BLOCKED_ERRORS as e:
            logger.error(f"IP ブロック中のため字幕取得を中断します (video_id={video_id}): {e}")
            raise

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
