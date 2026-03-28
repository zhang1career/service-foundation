import json
import logging
import time
from typing import Any, Dict, Tuple, Union

from app_aibroker.utils.callback_sign import callback_headers
from common.services.http import HttpCallError, request_async, request_sync

logger = logging.getLogger(__name__)


def deliver_callback(
        callback_url: str,
        callback_secret: str,
        body: Dict[str, Any],
        *,
        async_mode: bool = False,
) -> Union[Tuple[bool, int], str]:
    """
    POST callback with HMAC headers. Retries on 5xx/429/network error with exponential backoff.
    Returns (ok, last_status_code).
    """
    if not callback_url or not callback_secret:
        return False, 0

    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = callback_headers(callback_secret, raw)
    if async_mode:
        return request_async(
            method="POST",
            url=callback_url,
            pool_name="webhook_pool",
            queue_name="webhook",
            headers=headers,
            data=raw,
            timeout_sec=30,
        )

    max_attempts = 4
    delay = 0.5
    last_status = 0
    for attempt in range(max_attempts):
        try:
            resp = request_sync(
                method="POST",
                url=callback_url,
                pool_name="webhook_pool",
                headers=headers,
                data=raw,
                timeout_sec=30,
            )
            last_status = resp.status_code
            if resp.status_code < 500 and resp.status_code != 429:
                return True, last_status
        except HttpCallError as exc:
            logger.warning("[aibroker] callback attempt %s failed: %s", attempt + 1, exc)
        time.sleep(delay)
        delay = min(delay * 2, 8.0)
    return False, last_status
