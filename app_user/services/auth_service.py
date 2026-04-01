import json
from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

from common.utils.http_util import post
from app_user.repos import (
    get_user_by_login,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_phone,
    create_event,
    get_event_by_id,
    update_event_after_code,
    update_event_status,
)
from app_user.services.jwt_util import create_access_token, create_refresh_token, decode_token
from app_user.services.avatar_storage_service import upload_avatar
from app_user.enums import EventBizTypeEnum
from app_verify.enums import ChannelEnum, VerifyLevelEnum


def _get_integration_access_keys() -> tuple[str, str]:
    verify_access_key = (getattr(settings, "USER_VERIFY_ACCESS_KEY", "") or "").strip()
    notice_access_key = (getattr(settings, "USER_NOTICE_ACCESS_KEY", "") or "").strip()
    if not verify_access_key:
        raise ValueError("USER_VERIFY_ACCESS_KEY is required")
    if not notice_access_key:
        raise ValueError("USER_NOTICE_ACCESS_KEY is required")
    return verify_access_key, notice_access_key


def _mask_user(user) -> dict:
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


class AuthService:
    @staticmethod
    def register(username: str, password: str, email: str = "", phone: str = "", avatar=None, ext: Optional[dict] = None) -> dict:
        username = (username or "").strip()
        if not username or not password:
            raise ValueError("username and password are required")
        if get_user_by_username(username):
            raise ValueError("username already exists")
        if email and get_user_by_email(email):
            raise ValueError("email already exists")
        if phone and get_user_by_phone(phone):
            raise ValueError("phone already exists")

        avatar_url = upload_avatar(avatar) if avatar else ""
        user = create_user(username=username, password_hash=make_password(password), email=email, phone=phone, avatar=avatar_url, ext=ext)
        return AuthService._tokens(user)

    @staticmethod
    def login(login_key: str, password: str) -> dict:
        if not login_key or not password:
            raise ValueError("login_key and password are required")
        user = get_user_by_login(login_key.strip())
        if not user or user.status != 1:
            raise ValueError("invalid username/email/phone or password")
        if not check_password(password, user.password_hash):
            raise ValueError("invalid username/email/phone or password")
        return AuthService._tokens(user)

    @staticmethod
    def refresh(refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("invalid refresh token")
        user_id = payload.get("user_id")
        username = payload.get("username")
        if not user_id or not username:
            raise ValueError("invalid refresh token payload")
        return {
            "access_token": create_access_token(user_id=user_id, username=username),
        }

    @staticmethod
    def _request_password_reset(channel: str, target: str) -> bool:
        raise ValueError("password reset flow is removed")

    @staticmethod
    def request_password_reset_by_payload(payload: dict) -> dict:
        channel = (payload.get("channel") or "").strip()
        target = (payload.get("target") or "").strip()
        sent = AuthService._request_password_reset(channel=channel, target=target)
        return {"sent": sent}

    @staticmethod
    def _verify_password_reset(channel: str, target: str, code: str, new_password: str) -> bool:
        raise ValueError("password reset flow is removed")

    @staticmethod
    def verify_password_reset_by_payload(payload: dict) -> dict:
        channel = (payload.get("channel") or "").strip()
        target = (payload.get("target") or "").strip()
        code = (payload.get("code") or "").strip()
        new_password = payload.get("new_password") or ""
        reset = AuthService._verify_password_reset(
            channel=channel,
            target=target,
            code=code,
            new_password=new_password,
        )
        return {"reset": reset}

    @staticmethod
    def register_request_by_payload(payload: dict) -> dict:
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        email = (payload.get("email") or "").strip()
        phone = (payload.get("phone") or "").strip()
        avatar = payload.get("avatar")
        ext = payload.get("ext") if isinstance(payload.get("ext"), dict) else {}
        notice_channel = (payload.get("notice_channel") or "").strip().lower()
        notice_target = (payload.get("notice_target") or "").strip()
        if not notice_target:
            raise ValueError("notice_target is required")
        if notice_channel not in {"email", "sms"}:
            raise ValueError("notice_channel must be email or sms")
        if not username or not password:
            raise ValueError("username and password are required")
        if get_user_by_username(username):
            raise ValueError("username already exists")
        if email and get_user_by_email(email):
            raise ValueError("email already exists")
        if phone and get_user_by_phone(phone):
            raise ValueError("phone already exists")

        avatar_url = upload_avatar(avatar) if avatar else ""
        pending_payload = {
            "username": username,
            "password_hash": make_password(password),
            "email": email,
            "phone": phone,
            "avatar": avatar_url,
            "ext": ext,
        }
        event = create_event(
            biz_type=EventBizTypeEnum.REGISTER,
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
                "subject": "Register verify code",
                "content": f"Your register verify code is {code}. Event ID: {event.id}",
            },
        )
        if not notice_resp or notice_resp.get("errorCode") != 0:
            update_event_status(event.id, status=9, message="notice enqueue failed")
            raise ValueError("failed to enqueue notice")
        return {"event_id": event.id}

    @staticmethod
    def register_verify_by_payload(payload: dict) -> dict:
        event_id = int(payload.get("event_id") or 0)
        code = (payload.get("code") or "").strip()
        if event_id <= 0 or not code:
            raise ValueError("event_id and code are required")
        event = get_event_by_id(event_id)
        if not event or event.biz_type != EventBizTypeEnum.REGISTER or event.status != 1:
            raise ValueError("invalid event")
        verify_access_key, _ = _get_integration_access_keys()
        verify_resp = post(
            url=getattr(settings, "VERIFY_CHECK_URL"),
            data={
                "access_key": verify_access_key,
                "code_id": event.verify_code_id,
                "code": code,
            },
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(event.id, status=1, message="waiting for verified")
            raise ValueError("invalid or expired verify code")
        data = json.loads(event.payload_json or "{}")
        user = create_user(
            username=(data.get("username") or "").strip(),
            password_hash=data.get("password_hash") or "",
            email=(data.get("email") or "").strip(),
            phone=(data.get("phone") or "").strip(),
            avatar=data.get("avatar") or "",
            ext=data.get("ext") if isinstance(data.get("ext"), dict) else {},
        )
        user.status = 1
        user.save(using="user_rw", update_fields=["status"])
        update_event_status(event.id, status=3, message="completed")
        return AuthService._tokens(user)

    @staticmethod
    def _tokens(user) -> dict:
        return {
            "access_token": create_access_token(user_id=user.id, username=user.username),
            "refresh_token": create_refresh_token(user_id=user.id, username=user.username),
            "user": _mask_user(user),
        }
