from app_user.repos.token_repo import access_token_in_use
from app_user.utils.jwt_util import decode_token
from common.consts.response_const import RET_LOGIN_REQUIRED, RET_TOKEN_INVALID, RET_TOKEN_REVOKED
from common.utils.http_auth_util import authorization_header_from_request, parse_bearer_token


def client_ip_from_request(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def bearer_user_id_from_request(request):
    auth_header = authorization_header_from_request(request)
    token = parse_bearer_token(auth_header)
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
