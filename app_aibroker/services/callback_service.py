import json
import logging
import time
from typing import Any, Dict, Tuple

import requests

from app_aibroker.utils.callback_sign import callback_headers

logger = logging.getLogger(__name__)


def deliver_callback(callback_url: str, callback_secret: str, body: Dict[str, Any]) -> Tuple[bool, int]:
    """
    POST callback with HMAC headers. Retries on 5xx/429/network error with exponential backoff.
    Returns (ok, last_status_code).
    """
    if not callback_url or not callback_secret:
        return False, 0

    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = callback_headers(callback_secret, raw)
    max_attempts = 4
    delay = 0.5
    last_status = 0
    for attempt in range(max_attempts):
        try:
            resp = requests.post(callback_url, data=raw, headers=headers, timeout=30)
            last_status = resp.status_code
            if resp.status_code < 500 and resp.status_code != 429:
                return True, last_status
        except requests.RequestException as exc:
            logger.warning("[aibroker] callback attempt %s failed: %s", attempt + 1, exc)
        time.sleep(delay)
        delay = min(delay * 2, 8.0)
    return False, last_status
