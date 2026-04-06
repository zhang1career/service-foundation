from __future__ import annotations

import json
import logging
from enum import IntEnum

from django.conf import settings

from common.services.http import HttpCallError, HttpClientPool, request_sync
from common.utils.json_util import json_decode_from_bytes

logger = logging.getLogger(__name__)


class BrokerJiangEnum(IntEnum):
    WECHAT_SERVICE = 9
    WECOM_GROUP = 1
    WECOM_APP = 66
    DINGDING_GROUP = 2
    LARK_GROUP = 3

    @classmethod
    def send_message(cls, *, title: str, desp: str, channel: int) -> tuple[bool, str]:
        """
        Server酱 Turbo: POST {NOTICE_BROKER_JIANG_URL}/{NOTICE_BROKER_JIANG_SEND_KEY}.send
        JSON body: title, desp, channel (broker channel id as string per API).
        """
        base = str(settings.NOTICE_BROKER_JIANG_URL).rstrip("/")
        path_key = (settings.NOTICE_BROKER_JIANG_SEND_KEY or "").strip()
        if not path_key:
            return False, "NOTICE_BROKER_JIANG_SEND_KEY must be set"
        t = (title or "").strip()
        if not t:
            t = "Notice"
        desp = "" if desp is None else desp
        url = f"{base}/{path_key}.send"
        body = json.dumps(
            {"title": t, "desp": desp, "channel": str(int(channel))},
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            response = request_sync(
                method="POST",
                url=url,
                pool_name=HttpClientPool.THIRD_PARTY,
                headers={"Content-Type": "application/json; charset=utf-8"},
                data=body,
                timeout_sec=15,
            )
        except HttpCallError as exc:
            logger.warning("[BrokerJiangEnum] http error: %s", exc)
            return False, str(exc)

        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"

        parsed = json_decode_from_bytes(response.content)
        if not isinstance(parsed, dict):
            return False, "invalid response body"
        code = parsed.get("code")
        if code == 0:
            return True, "ok"
        msg = parsed.get("message")
        if msg is not None and str(msg).strip():
            return False, str(msg)
        return False, "send failed"
