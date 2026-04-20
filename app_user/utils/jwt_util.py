from typing import Any, Optional

import jwt
from django.conf import settings

from common.utils.jwt_codec import claims_with_expiry, decode_hs256_token, encode_hs256_token

ACCESS_TOKEN_TTL_SECONDS = 2 * 60 * 60
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60


def jwt_signing_secret() -> str:
    configured = getattr(settings, "JWT_SECRET", None)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return settings.SECRET_KEY


def create_access_token(user_id: int, username: str) -> str:
    claims = claims_with_expiry(
        {"type": "access", "user_id": user_id, "username": username},
        ACCESS_TOKEN_TTL_SECONDS,
    )
    return encode_hs256_token(claims, jwt_signing_secret())


def create_refresh_token(user_id: int, username: str) -> str:
    claims = claims_with_expiry(
        {"type": "refresh", "user_id": user_id, "username": username},
        REFRESH_TOKEN_TTL_SECONDS,
    )
    return encode_hs256_token(claims, jwt_signing_secret())


def decode_token(token: str) -> Optional[dict]:
    return decode_hs256_token(token, jwt_signing_secret())


def decode_access_token_light(token: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Signature + exp + access claims only; no DB. ``(claims, None)`` or ``(None, "expired"|"invalid")``."""
    if not token:
        return None, "invalid"
    try:
        claims = jwt.decode(token, jwt_signing_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None, "expired"
    except jwt.InvalidTokenError:
        return None, "invalid"
    if claims.get("type") != "access" or not claims.get("user_id"):
        return None, "invalid"
    return claims, None


def access_expires_at_ms_from_token(access_token: str) -> int:
    payload = decode_token(access_token)
    if not payload or "exp" not in payload:
        raise ValueError("access token missing exp")
    return int(payload["exp"]) * 1000
