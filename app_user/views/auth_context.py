from app_user.services.jwt_util import decode_token
from common.consts.response_const import RET_LOGIN_REQUIRED, RET_TOKEN_INVALID
from common.utils.http_auth_util import authorization_header_from_request, parse_bearer_token


def bearer_user_id_from_request(request):
    auth_header = authorization_header_from_request(request)
    token = parse_bearer_token(auth_header)
    if not token:
        return None, RET_LOGIN_REQUIRED, "login required"
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None, RET_TOKEN_INVALID, "invalid token"
    return payload.get("user_id"), 0, ""
