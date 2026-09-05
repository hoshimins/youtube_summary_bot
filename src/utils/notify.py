import os
import requests
from utils.logger import get_logger

logger = get_logger(__name__)


def notify_failure(title: str, message: str, priority: str = "high") -> bool:
    """ntfy へ失敗通知を送る。未設定なら何もしない。

    環境変数:
      NTFY_URL   例: https://ntfy.example.com/youtube-summary-bot
      NTFY_TOKEN 任意。Bearer トークン
    """
    url = (os.getenv("NTFY_URL") or "").strip()
    if not url:
        return False

    headers = {
        "Title": title[:250],
        "Priority": priority,
        "Tags": "warning,youtube_summary_bot",
    }
    token = (os.getenv("NTFY_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            url,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error(
                f"ntfy 通知失敗: status={response.status_code}, body={response.text}"
            )
            return False
        logger.info(f"ntfy 通知を送信しました: {title}")
        return True
    except Exception as e:
        logger.error(f"ntfy 通知エラー: {e}")
        return False
