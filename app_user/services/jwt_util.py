from typing import Optional

from django.conf import settings

from common.utils.jwt_codec import (
    claims_with_expiry,
    decode_hs256_token,
    encode_hs256_token,
)

ACCESS_TOKEN_TTL_SECONDS = 2 * 60 * 60
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60


def _secret() -> str:
    configured = getattr(settings, "JWT_SECRET", None)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return settings.SECRET_KEY


def create_access_token(user_id: int, username: str) -> str:
    claims = claims_with_expiry(
        {"type": "access", "user_id": user_id, "username": username},
        ACCESS_TOKEN_TTL_SECONDS,
    )
    return encode_hs256_token(claims, _secret())


def create_refresh_token(user_id: int, username: str) -> str:
    claims = claims_with_expiry(
        {"type": "refresh", "user_id": user_id, "username": username},
        REFRESH_TOKEN_TTL_SECONDS,
    )
    return encode_hs256_token(claims, _secret())


def decode_token(token: str) -> Optional[dict]:
    return decode_hs256_token(token, _secret())
