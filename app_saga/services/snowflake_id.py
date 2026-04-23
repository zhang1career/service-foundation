import logging
from typing import Any

import httpx
from django.conf import settings

from common.consts.response_const import RET_OK
from common.services.http import HttpClientPool, request_sync
from common.services.service_discovery import expand_service_discovery_url
from common.utils.service_url_template import ServiceUrlResolutionError

logger = logging.getLogger(__name__)


class SnowflakeIdError(RuntimeError):
    pass


def allocate_snowflake_int() -> int:
    url = (settings.SAGA_SNOWFLAKE_ID_URL or "").strip()
    if not url:
        raise SnowflakeIdError("SAGA_SNOWFLAKE_ID_URL is not configured")
    try:
        url = expand_service_discovery_url(url)
    except ServiceUrlResolutionError as e:
        raise SnowflakeIdError(str(e)) from e
    access_key = (settings.SAGA_SNOWFLAKE_ACCESS_KEY or "").strip()
    if not access_key:
        raise SnowflakeIdError("SAGA_SNOWFLAKE_ACCESS_KEY is not configured")
    timeout = float(settings.SAGA_SNOWFLAKE_HTTP_TIMEOUT_SEC)
    try:
        resp = request_sync(
            method="POST",
            url=url,
            json_body={"access_key": access_key},
            pool_name=HttpClientPool.THIRD_PARTY,
            timeout_sec=timeout,
        )
    except httpx.HTTPError as e:
        logger.warning("saga snowflake id request failed: %s", e)
        raise SnowflakeIdError("snowflake HTTP request failed") from e

    if resp.status_code < 200 or resp.status_code >= 300:
        raise SnowflakeIdError(f"snowflake HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        envelope: dict[str, Any] = resp.json()
    except ValueError as e:
        raise SnowflakeIdError("snowflake response is not JSON") from e

    if int(envelope.get("errorCode", -1)) != RET_OK:
        raise SnowflakeIdError(envelope.get("message") or "snowflake errorCode !=0")

    data = envelope.get("data")
    if not isinstance(data, dict):
        raise SnowflakeIdError("snowflake data missing")
    sid = data.get("id")
    if sid is None or str(sid).strip() == "":
        raise SnowflakeIdError("snowflake data.id missing")
    try:
        return int(str(sid).strip())
    except ValueError as e:
        raise SnowflakeIdError("snowflake data.id is not an integer") from e
