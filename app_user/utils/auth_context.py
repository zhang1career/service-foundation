from app_user.repos.token_repo import access_token_in_use
from app_user.utils.jwt_util import decode_token
from common.consts.response_const import RET_LOGIN_REQUIRED, RET_TOKEN_INVALID, RET_TOKEN_REVOKED

# Inbound JWT for /me* (and related) APIs: raw token string, not ``Authorization: Bearer``.
USER_ACCESS_TOKEN_HEADER = "X-User-Access-Token"


def client_ip_from_request(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def user_access_token_from_request(request) -> str | None:
    """Return the app_user access JWT from ``X-User-Access-Token`` (raw value, no ``Bearer`` prefix)."""
    raw = request.META.get("HTTP_X_USER_ACCESS_TOKEN", "")
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    return token if token else None


def bearer_user_id_from_request(request):
    token = user_access_token_from_request(request)
    if not token:
        return None, RET_LOGIN_REQUIRED, "login required"
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None, RET_TOKEN_INVALID, "invalid token"
    user_id = payload.get("user_id")
    if not user_id:
        return None, RET_TOKEN_INVALID, "invalid token"
    if not access_token_in_use(user_id=user_id, access_token=token):
        return None, RET_TOKEN_REVOKED, "token revoked or expired"
    return user_id, 0, ""
