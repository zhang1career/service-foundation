from typing import Optional
import json

from django.conf import settings

from app_user.enums import EventBizTypeEnum
from app_verify.enums import ChannelEnum, VerifyLevelEnum
from common.consts.query_const import LIMIT_PAGE, LIMIT_LIST
from common.utils.page_util import build_page
from common.utils.http_util import post
from app_user.repos import (
    get_user_by_id,
    get_user_by_username,
    get_user_by_email,
    get_user_by_phone,
    update_user_profile,
    list_users,
    update_user_status,
    update_user_auth_status,
    create_event,
    get_event_by_id,
    update_event_after_code,
    update_event_status,
)
from app_user.services.avatar_storage_service import upload_avatar
from django.contrib.auth.hashers import make_password
from app_user.enums import UserStatusEnum


def _get_integration_access_keys() -> tuple[str, str]:
    verify_access_key = (getattr(settings, "USER_VERIFY_ACCESS_KEY", "") or "").strip()
    notice_access_key = (getattr(settings, "USER_NOTICE_ACCESS_KEY", "") or "").strip()
    if not verify_access_key:
        raise ValueError("USER_VERIFY_ACCESS_KEY is required")
    if not notice_access_key:
        raise ValueError("USER_NOTICE_ACCESS_KEY is required")
    return verify_access_key, notice_access_key


def _to_dict(user) -> dict:
    try:
        ext_data = json.loads(user.ext or "{}")
    except (TypeError, ValueError):
        ext_data = {}
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "phone": user.phone or "",
        "avatar": user.avatar,
        "status": user.status,
        "auth_status": getattr(user, "auth_status", 0) or 0,
        "ext": ext_data,
        "ct": user.ct,
        "ut": user.ut,
    }

AUTH_BIT_VERIFY_CODE = 1 << 0


class UserService:
    @staticmethod
    def get_me(user_id: int) -> Optional[dict]:
        user = get_user_by_id(user_id)
        if not user:
            return None
        return _to_dict(user)

    @staticmethod
    def update_me(user_id: int, email: Optional[str], phone: Optional[str], avatar, ext: Optional[dict]) -> Optional[dict]:
        avatar_url = None
        if avatar is not None:
            avatar_url = upload_avatar(avatar) if avatar else ""
        user = update_user_profile(user_id=user_id, email=email, phone=phone, avatar=avatar_url, ext=ext)
        if not user:
            return None
        return _to_dict(user)

    @staticmethod
    def update_me_request_by_payload(user_id: int, payload: dict) -> dict:
        notice_channel = (payload.get("notice_channel") or "").strip().lower()
        notice_target = (payload.get("notice_target") or "").strip()
        if notice_channel not in {"email", "sms"}:
            raise ValueError("notice_channel must be email or sms")
        if not notice_target:
            raise ValueError("notice_target is required")
        pending_payload = {
            "email": (payload.get("email") or "").strip() if "email" in payload else None,
            "phone": (payload.get("phone") or "").strip() if "phone" in payload else None,
            "avatar": (payload.get("avatar") or "").strip() if "avatar" in payload else None,
            "ext": payload.get("ext") if isinstance(payload.get("ext"), dict) else None,
        }
        event = create_event(
            biz_type=EventBizTypeEnum.UPDATE_PROFILE,
            level=VerifyLevelEnum.HIGH.value,
            notice_channel=ChannelEnum.from_label(notice_channel),
            notice_target=notice_target,
            payload_json=json.dumps(pending_payload, ensure_ascii=False),
        )
        verify_access_key, notice_access_key = _get_integration_access_keys()
        verify_resp = post(
            url=getattr(settings, "VERIFY_REQUEST_URL"),
            data={
                "access_key": verify_access_key,
                "level": VerifyLevelEnum.HIGH.value,
                "ref_id": event.id,
            },
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(event.id, status=9, message="verify request failed")
            raise ValueError("failed to request verify code")
        verify_data = verify_resp.get("data") or {}
        code = verify_data.get("code")
        code_id = int(verify_data.get("code_id") or 0)
        ref_id = int(verify_data.get("ref_id") or 0)
        if not code or code_id <= 0 or ref_id != event.id:
            update_event_status(event.id, status=9, message="invalid verify response")
            raise ValueError("invalid verify response")
        update_event_after_code(event.id, verify_code_id=code_id, verify_ref_id=ref_id)
        notice_resp = post(
            url=getattr(settings, "NOTICE_SERVICE_URL"),
            data={
                "access_key": notice_access_key,
                "event_id": event.id,
                "channel": ChannelEnum.from_label(notice_channel),
                "target": notice_target,
                "subject": "Update profile verify code",
                "content": f"Your verify code is {code}. Event ID: {event.id}",
            },
        )
        if not notice_resp or notice_resp.get("errorCode") != 0:
            update_event_status(event.id, status=9, message="notice enqueue failed")
            raise ValueError("failed to enqueue notice")
        return {"event_id": event.id}

    @staticmethod
    def update_me_verify_by_payload(user_id: int, payload: dict) -> Optional[dict]:
        event_id = int(payload.get("event_id") or 0)
        code = (payload.get("code") or "").strip()
        if event_id <= 0 or not code:
            raise ValueError("event_id and code are required")
        event = get_event_by_id(event_id)
        if not event or event.biz_type != EventBizTypeEnum.UPDATE_PROFILE or event.status != 1:
            raise ValueError("invalid event")
        verify_access_key, _ = _get_integration_access_keys()
        verify_resp = post(
            url=getattr(settings, "VERIFY_CHECK_URL"),
            data={
                "access_key": verify_access_key,
                "code_id": event.verify_code_id,
                "code": code,
                "level": event.level,
            },
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(event.id, status=1, message="waiting for verified")
            raise ValueError("invalid or expired verify code")
        data = json.loads(event.payload_json or "{}")
        user = update_user_profile(
            user_id=user_id,
            email=data.get("email"),
            phone=data.get("phone"),
            avatar=data.get("avatar"),
            ext=data.get("ext"),
        )
        update_event_status(event.id, status=3, message="completed")
        return _to_dict(user) if user else None

    @staticmethod
    def list_users(offset: int = 0, limit: int = LIMIT_PAGE) -> dict:
        if limit <= 0:
            limit = LIMIT_PAGE
        if limit > LIMIT_LIST:
            limit = LIMIT_LIST
        users, total = list_users(offset=offset, limit=limit)
        data = [_to_dict(item) for item in users]
        next_offset = offset + limit if offset + limit < total else None
        return build_page(data_list=data, next_offset=next_offset, total_num=total)

    @staticmethod
    def set_status(user_id: int, status: int) -> Optional[dict]:
        user = update_user_status(user_id=user_id, status=status)
        if not user:
            return None
        return _to_dict(user)

    @staticmethod
    def console_create_user_by_payload(payload: dict) -> dict:
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        email = (payload.get("email") or "").strip()
        phone = (payload.get("phone") or "").strip()
        notice_channel = (payload.get("notice_channel") or "").strip().lower()
        notice_target = (payload.get("notice_target") or "").strip()
        status = int(payload.get("status", UserStatusEnum.ENABLED.value if hasattr(UserStatusEnum, "ENABLED") else 1))
        ext = payload.get("ext") if isinstance(payload.get("ext"), dict) else {}
        if not username or not password:
            raise ValueError("username and password are required")
        if get_user_by_username(username):
            raise ValueError("username already exists")
        if email and get_user_by_email(email):
            raise ValueError("email already exists")
        if phone and get_user_by_phone(phone):
            raise ValueError("phone already exists")

        # notice defaults: follow email/phone if not explicitly provided
        if not notice_target:
            if email:
                notice_channel, notice_target = "email", email
            elif phone:
                notice_channel, notice_target = "sms", phone
        if not notice_target:
            raise ValueError("notice_target is required (email or phone)")
        if notice_channel not in {"email", "sms"}:
            raise ValueError("notice_channel must be email or sms")

        from app_user.repos import create_user  # avoid circular import in some runtimes

        avatar_url = ""
        if "avatar" in payload and payload.get("avatar"):
            avatar_url = upload_avatar(payload.get("avatar"))

        user = create_user(
            username=username,
            password_hash=make_password(password),
            email=email,
            phone=phone,
            avatar=avatar_url,
            ext=ext,
        )
        # console created users are enabled by default
        if user.status != status:
            user.status = status
            user.save(using="user_rw", update_fields=["status"])

        # Send verify code immediately
        verify_access_key, notice_access_key = _get_integration_access_keys()
        event = create_event(
            biz_type=EventBizTypeEnum.USER_AUTH,
            level=VerifyLevelEnum.HIGH.value,
            notice_channel=ChannelEnum.from_label(notice_channel),
            notice_target=notice_target,
            payload_json=json.dumps({"user_id": user.id, "bit": AUTH_BIT_VERIFY_CODE}, ensure_ascii=False),
        )
        verify_resp = post(
            url=getattr(settings, "VERIFY_REQUEST_URL"),
            data={
                "access_key": verify_access_key,
                "level": VerifyLevelEnum.HIGH.value,
                "ref_id": event.id,
            },
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(event.id, status=9, message="verify request failed")
            raise ValueError("failed to request verify code")
        verify_data = verify_resp.get("data") or {}
        code = verify_data.get("code")
        code_id = int(verify_data.get("code_id") or 0)
        ref_id = int(verify_data.get("ref_id") or 0)
        if not code or code_id <= 0 or ref_id != event.id:
            update_event_status(event.id, status=9, message="invalid verify response")
            raise ValueError("invalid verify response")
        update_event_after_code(event.id, verify_code_id=code_id, verify_ref_id=ref_id)
        notice_resp = post(
            url=getattr(settings, "NOTICE_SERVICE_URL"),
            data={
                "access_key": notice_access_key,
                "event_id": event.id,
                "channel": ChannelEnum.from_label(notice_channel),
                "target": notice_target,
                "subject": "User verify code",
                "content": f"Your verify code is {code}. User ID: {user.id}",
            },
        )
        if not notice_resp or notice_resp.get("errorCode") != 0:
            update_event_status(event.id, status=9, message="notice enqueue failed")
            raise ValueError("failed to enqueue notice")

        return {"user": _to_dict(user), "event_id": event.id}

    @staticmethod
    def _find_latest_pending_user_auth_event(user_id: int):
        from app_user.models import Event
        # best-effort query: payload_json contains user_id and status=1 means code sent & pending verify
        needle = f'"user_id": {int(user_id)}'
        return (
            Event.objects.using("user_rw")
            .filter(biz_type=EventBizTypeEnum.USER_AUTH, status=1, payload_json__contains=needle)
            .order_by("-ct")
            .first()
        )

    @staticmethod
    def console_verify_user_by_code(user_id: int, code: str) -> dict:
        code = (code or "").strip()
        if not code:
            raise ValueError("code is required")
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        event = UserService._find_latest_pending_user_auth_event(user_id=user_id)
        if not event:
            raise ValueError("没有待认证的验证码事件，请先在用户列表新建用户并发送验证码，或重新触发验证码下发")
        verify_access_key, _ = _get_integration_access_keys()
        verify_resp = post(
            url=getattr(settings, "VERIFY_CHECK_URL"),
            data={
                "access_key": verify_access_key,
                "code_id": event.verify_code_id,
                "code": code,
                "level": event.level,
            },
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(event.id, status=1, message="waiting for verified")
            raise ValueError("验证码无效或已过期")

        # mark auth bit
        new_mask = (getattr(user, "auth_status", 0) or 0) | AUTH_BIT_VERIFY_CODE
        updated = update_user_auth_status(user_id=user.id, auth_status=new_mask)
        update_event_status(event.id, status=3, message="completed")
        return {"user": _to_dict(updated or user), "auth_status": new_mask}

    @staticmethod
    def console_update_user_by_payload(user_id: int, payload: dict) -> Optional[dict]:
        # edit page: does not support auth operations
        email = (payload.get("email") or "").strip() if "email" in payload else None
        phone = (payload.get("phone") or "").strip() if "phone" in payload else None
        avatar = None
        if "avatar" in payload:
            raw = payload.get("avatar")
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                avatar = ""
            else:
                avatar = upload_avatar(raw)
        ext = payload.get("ext") if isinstance(payload.get("ext"), dict) else None if "ext" in payload else None
        status = int(payload.get("status")) if "status" in payload else None

        user = update_user_profile(user_id=user_id, email=email, phone=phone, avatar=avatar, ext=ext)
        if status is not None:
            user = update_user_status(user_id=user_id, status=status)
        return _to_dict(user) if user else None
