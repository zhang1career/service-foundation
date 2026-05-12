from typing import Optional

from rest_framework.views import APIView

from app_user.services import AuthService, EventService, UserService
from app_user.utils.auth_context import bearer_user_id_from_request, user_access_token_from_request
from app_user.utils.jwt_util import decode_access_token_light
from common.consts.query_const import LIMIT_LIST, LIMIT_PAGE
from common.consts.response_const import (
    RET_INVALID_PARAM,
    RET_LOGIN_REQUIRED,
    RET_RESOURCE_NOT_FOUND,
    RET_TOKEN_EXPIRED,
    RET_TOKEN_INVALID,
)
from common.utils.http_util import resp_ok, resp_err, with_type


def _optional_user_ids_param(query) -> tuple[Optional[list[int]], Optional[str]]:
    """Parses GET ``user_ids`` (comma-separated). Absent or blank → ``(None, None)``."""
    if "user_ids" not in query:
        return None, None
    raw = query.get("user_ids")
    if raw is None or not str(raw).strip():
        return None, None
    stripped = str(raw).strip()
    ids: list[int] = []
    seen: set[int] = set()
    for token in stripped.split(","):
        part = token.strip()
        if not part:
            continue
        try:
            uid = int(part)
        except ValueError:
            return None, "user_ids must be comma-separated positive integers"
        if uid < 1:
            return None, "user_ids must be comma-separated positive integers"
        if uid in seen:
            continue
        seen.add(uid)
        ids.append(uid)
        if len(ids) > LIMIT_LIST:
            return None, f"user_ids must contain at most {LIMIT_LIST} distinct ids"
    if not ids:
        return None, None
    return ids, None


class UserJwtValidateView(APIView):
    """校验 access JWT（须含 user_id、auth_status）；不查 token 表。"""

    def get(self, request, *args, **kwargs):
        token = user_access_token_from_request(request)
        if not token:
            return resp_err(code=RET_LOGIN_REQUIRED, message="login required")
        claims, err = decode_access_token_light(token)
        if err == "expired":
            return resp_err(code=RET_TOKEN_EXPIRED, message="token expired")
        if err or not claims:
            return resp_err(code=RET_TOKEN_INVALID, message="invalid token")
        return resp_ok(
            {
                "user_id": claims["user_id"],
                "username": claims.get("username"),
                "permissions": [],
                "auth_status": claims["auth_status"],
            }
        )


class UserMeView(APIView):
    def get(self, request, *args, **kwargs):
        user_id, code, message = bearer_user_id_from_request(request)
        if not user_id:
            return resp_err(code=code, message=message)
        user = UserService.get_me(user_id=user_id)
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)

    def patch(self, request, *args, **kwargs):
        user_id, code, message = bearer_user_id_from_request(request)
        if not user_id:
            return resp_err(code=code, message=message)
        data = request.data if hasattr(request, "data") else request.POST
        avatar = data.get("avatar") if "avatar" in data else None
        if hasattr(request, "FILES") and request.FILES.get("avatar"):
            avatar = request.FILES.get("avatar")
        user = UserService.update_me(
            user_id=user_id,
            email=data.get("email") if "email" in data else None,
            phone=data.get("phone") if "phone" in data else None,
            avatar=avatar,
            ext=data.get("ext") if "ext" in data else None,
        )
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)


class UserMeUpdateRequestView(APIView):
    def post(self, request, *args, **kwargs):
        user_id, code, message = bearer_user_id_from_request(request)
        if not user_id:
            return resp_err(code=code, message=message)
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(UserService.update_me_request_by_payload(user_id=user_id, payload=data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class UserMeUpdateVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        user_id, code, message = bearer_user_id_from_request(request)
        if not user_id:
            return resp_err(code=code, message=message)
        data = request.data if hasattr(request, "data") else request.POST
        try:
            user = UserService.update_me_verify_by_payload(user_id=user_id, payload=data)
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)


class UserListView(APIView):
    def get(self, request, *args, **kwargs):
        offset = with_type(request.GET.get("offset", 0))
        limit = with_type(request.GET.get("limit", LIMIT_PAGE))
        user_ids, uid_err = _optional_user_ids_param(request.GET)
        if uid_err:
            return resp_err(code=RET_INVALID_PARAM, message=uid_err)
        page = UserService.list_users(offset=offset, limit=limit, user_ids=user_ids)
        return resp_ok(page)


class UserDetailView(APIView):
    def get(self, request, user_id, *args, **kwargs):
        user = UserService.get_me(user_id=with_type(user_id))
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)


class UserConsoleListView(APIView):
    """
    控制台新建用户：
    - 直接插入 user 记录（auth_status=0）
    - 触发验证码下发（verify + notice）
    """

    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        payload = _extract_console_payload(data)
        if hasattr(request, "FILES") and request.FILES.get("avatar"):
            payload["avatar"] = request.FILES.get("avatar")
        # Keep console create flow consistent with public register:
        # create register event first, then create user after verify passed.
        email = (payload.get("email") or "").strip()
        phone = (payload.get("phone") or "").strip()
        if not payload.get("notice_target"):
            if email:
                payload["notice_channel"] = "email"
                payload["notice_target"] = email
            elif phone:
                payload["notice_channel"] = "sms"
                payload["notice_target"] = phone
        try:
            return resp_ok(AuthService.register_request_by_payload(payload))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class UserConsoleVerifyView(APIView):
    """控制台用户认证：仅提交验证码 code（后端自动寻找最新待认证事件）。"""

    def post(self, request, user_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            result = UserService.console_verify_user_by_code(
                user_id=with_type(user_id),
                code=data.get("code"),
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
        return resp_ok(result)


class UserConsoleDispositionRestoreView(APIView):
    """控制台：清除安全处置状态（不恢复已废止的 token）。"""

    def post(self, request, user_id, *args, **kwargs):
        user = UserService.console_clear_disposition(user_id=with_type(user_id))
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)


class UserConsoleDetailView(APIView):
    """控制台用户：GET 含完整 ctrl_reason；PATCH 编辑（不支持认证状态修改）。"""

    def get(self, request, user_id, *args, **kwargs):
        user = UserService.console_get_user(user_id=with_type(user_id))
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)

    def patch(self, request, user_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        payload = _extract_console_payload(data)
        if hasattr(request, "FILES") and request.FILES.get("avatar"):
            payload["avatar"] = request.FILES.get("avatar")
        user = UserService.console_update_user_by_payload(user_id=with_type(user_id), payload=payload)
        if not user:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="user not found")
        return resp_ok(user)


def _extract_console_payload(data) -> dict:
    payload = {}
    for key in ("username", "password", "email", "phone", "status", "notice_channel", "notice_target"):
        if key in data:
            payload[key] = data.get(key)
    if "ext" in data:
        payload["ext"] = data.get("ext")
    if "avatar" in data:
        payload["avatar"] = data.get("avatar")
    return payload


class EventConsoleListView(APIView):
    def get(self, request, *args, **kwargs):
        offset = with_type(request.GET.get("offset", 0))
        limit = with_type(request.GET.get("limit", LIMIT_PAGE))
        return resp_ok(EventService.list_events(offset=offset, limit=limit))


class EventConsoleDetailView(APIView):
    def get(self, request, event_id, *args, **kwargs):
        event = EventService.get_event(event_id=with_type(event_id))
        if not event:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="event not found")
        return resp_ok(event)

    def patch(self, request, event_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        event = EventService.update_event_by_payload(event_id=with_type(event_id), payload=dict(data))
        if not event:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="event not found")
        return resp_ok(event)

    def delete(self, request, event_id, *args, **kwargs):
        ok = EventService.delete_event(event_id=with_type(event_id))
        if not ok:
            return resp_err(code=RET_RESOURCE_NOT_FOUND, message="event not found")
        return resp_ok({"deleted": True, "id": with_type(event_id)})
