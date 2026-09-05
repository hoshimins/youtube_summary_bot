import os
from utils.logger import get_logger

logger = get_logger(__name__)


def prepare_caption_for_storage(caption: str) -> str:
    """字幕を DB / 要約向けに正規化し、最大文字数で切り詰める。"""
    text = " ".join(caption.split()).strip()
    if not text:
        return text

    max_chars = int(os.getenv("CAPTION_MAX_CHARS", "100000"))
    if len(text) > max_chars:
        logger.warning(
            f"字幕が長すぎるため {max_chars} 文字に切り詰めます (元: {len(text)} 文字)"
        )
        text = text[:max_chars]

    return text
