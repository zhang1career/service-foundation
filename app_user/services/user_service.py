import json
from typing import Optional

from app_user.enums import EventBizTypeEnum, EventStatusEnum
from app_user.repos import (
    get_user_by_id,
    list_users,
    update_event_status,
    update_user_auth_status,
    update_user_profile,
    update_user_status,
)
from app_user.services.avatar_storage_service import upload_avatar
from app_user.services.user_serialization import user_to_public_dict
from app_user.services.verify_notice_integration import (
    create_verify_event_and_send_notice,
    load_verify_notice_access_keys,
    post_verify_check,
    verify_payload_code_for_pending_event,
)
from app_verify.enums import ChannelEnum, VerifyLevelEnum
from common.consts.query_const import LIMIT_LIST, LIMIT_PAGE
from common.utils.page_util import build_page


AUTH_BIT_VERIFY_CODE = 1 << 0


class UserService:
    @staticmethod
    def get_me(user_id: int) -> Optional[dict]:
        user = get_user_by_id(user_id)
        if not user:
            return None
        return user_to_public_dict(user)

    @staticmethod
    def update_me(user_id: int, email: Optional[str], phone: Optional[str], avatar, ext: Optional[dict]) -> Optional[dict]:
        avatar_url = None
        if avatar is not None:
            avatar_url = upload_avatar(avatar) if avatar else ""
        user = update_user_profile(user_id=user_id, email=email, phone=phone, avatar=avatar_url, ext=ext)
        if not user:
            return None
        return user_to_public_dict(user)

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
        event = create_verify_event_and_send_notice(
            biz_type=EventBizTypeEnum.UPDATE_PROFILE,
            level=VerifyLevelEnum.HIGH.value,
            notice_channel=ChannelEnum.from_label(notice_channel),
            notice_target=notice_target,
            payload_json=json.dumps(pending_payload, ensure_ascii=False),
            subject="Update profile verify code",
            content_template="Your verify code is {code}. Event ID: {event_id}",
        )
        return {"event_id": event.id}

    @staticmethod
    def update_me_verify_by_payload(user_id: int, payload: dict) -> Optional[dict]:
        event, data = verify_payload_code_for_pending_event(
            payload=payload,
            expected_biz_type=EventBizTypeEnum.UPDATE_PROFILE,
        )
        user = update_user_profile(
            user_id=user_id,
            email=data.get("email"),
            phone=data.get("phone"),
            avatar=data.get("avatar"),
            ext=data.get("ext"),
        )
        update_event_status(event.id, status=EventStatusEnum.COMPLETED.value, message="completed")
        return user_to_public_dict(user) if user else None

    @staticmethod
    def list_users(offset: int = 0, limit: int = LIMIT_PAGE) -> dict:
        if limit <= 0:
            limit = LIMIT_PAGE
        if limit > LIMIT_LIST:
            limit = LIMIT_LIST
        users, total = list_users(offset=offset, limit=limit)
        data = [user_to_public_dict(item) for item in users]
        next_offset = offset + limit if offset + limit < total else None
        return build_page(data_list=data, next_offset=next_offset, total_num=total)

    @staticmethod
    def set_status(user_id: int, status: int) -> Optional[dict]:
        user = update_user_status(user_id=user_id, status=status)
        if not user:
            return None
        return user_to_public_dict(user)

    @staticmethod
    def _find_latest_pending_user_auth_event(user_id: int):
        from app_user.models import Event

        needle = f'"user_id": {int(user_id)}'
        return (
            Event.objects.using("user_rw")
            .filter(
                biz_type=EventBizTypeEnum.USER_AUTH,
                status=EventStatusEnum.PENDING_VERIFY.value,
                payload_json__contains=needle,
            )
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
        verify_access_key, _ = load_verify_notice_access_keys()
        verify_resp = post_verify_check(
            verify_access_key=verify_access_key,
            code_id=event.verify_code_id,
            code=code,
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            update_event_status(
                event.id,
                status=EventStatusEnum.PENDING_VERIFY.value,
                message="waiting for verified",
            )
            raise ValueError("验证码无效或已过期")

        new_mask = (getattr(user, "auth_status", 0) or 0) | AUTH_BIT_VERIFY_CODE
        updated = update_user_auth_status(user_id=user.id, auth_status=new_mask)
        update_event_status(event.id, status=EventStatusEnum.COMPLETED.value, message="completed")
        return {"user": user_to_public_dict(updated or user), "auth_status": new_mask}

    @staticmethod
    def console_update_user_by_payload(user_id: int, payload: dict) -> Optional[dict]:
        email = (payload.get("email") or "").strip() if "email" in payload else None
        phone = (payload.get("phone") or "").strip() if "phone" in payload else None
        avatar = None
        if "avatar" in payload:
            raw = payload.get("avatar")
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                avatar = ""
            else:
                avatar = upload_avatar(raw)
        ext = None
        if "ext" in payload:
            raw_ext = payload.get("ext")
            ext = raw_ext if isinstance(raw_ext, dict) else None
        status = int(payload.get("status")) if "status" in payload else None

        user = update_user_profile(user_id=user_id, email=email, phone=phone, avatar=avatar, ext=ext)
        if status is not None:
            user = update_user_status(user_id=user_id, status=status)
        return user_to_public_dict(user) if user else None
