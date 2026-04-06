from __future__ import annotations

from enum import Enum


class HttpClientPool(str, Enum):
    """Stable httpx client pool identifiers (wire / logs / Celery JSON)."""
    THIRD_PARTY = "3rd_party_pl"
    WEBHOOK = "webhook_pl"


def pool_id(value: HttpClientPool | str | None) -> str:
    """Normalize pool to the wire string; empty or missing → default pool."""
    if value is None or value == "":
        return HttpClientPool.THIRD_PARTY.value
    if isinstance(value, HttpClientPool):
        return value.value
    return value
