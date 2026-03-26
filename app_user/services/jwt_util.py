import time
from typing import Optional

import jwt
from django.conf import settings


ACCESS_TOKEN_TTL_SECONDS = 2 * 60 * 60
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60


def _secret() -> str:
    return getattr(settings, "JWT_SECRET", "") or settings.SECRET_KEY


def create_access_token(user_id: int, username: str) -> str:
    now = int(time.time())
    payload = {
        "type": "access",
        "user_id": user_id,
        "username": username,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def create_refresh_token(user_id: int, username: str) -> str:
    now = int(time.time())
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "username": username,
        "iat": now,
        "exp": now + REFRESH_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    if not token:
        return None
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None


def parse_bearer_token(auth_header: str) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()
