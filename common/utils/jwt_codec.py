"""JWT encode/decode helpers with explicit secret and claims (no Django settings).

Currently uses HMAC-SHA256 (HS256); callers pass the shared secret string.
"""

from __future__ import annotations

import time
from typing import Any

import jwt


def encode_hs256_token(claims: dict[str, Any], secret: str) -> str:
    return jwt.encode(claims, secret, algorithm="HS256")


def decode_hs256_token(token: str, secret: str) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None


def claims_with_expiry(
    claims: dict[str, Any],
    ttl_seconds: int,
    *,
    now: int | None = None,
) -> dict[str, Any]:
    """Return a new dict with ``iat`` and ``exp`` set; overwrites any existing ``iat``/``exp`` in ``claims``."""
    t = int(time.time()) if now is None else now
    return {**claims, "iat": t, "exp": t + ttl_seconds}
