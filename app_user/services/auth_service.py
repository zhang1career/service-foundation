import json

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction

from app_user.enums import (
    EventBizTypeEnum,
    EventStatusEnum,
    UserDispositionEnum,
    UserStatusEnum,
)
from app_user.repos import (
    cancel_pending_events_by_notice,
    create_user,
    get_event_by_id,
    get_user_by_email,
    get_user_by_id,
    get_user_by_login,
    get_user_by_phone,
    get_user_by_username,
    get_latest_incomplete_event_by_notice,
    update_event_status,
    update_user_password,
)
from app_user.repos.token_repo import (
    deprecate_all_tokens_for_user,
    refresh_token_in_use,
    replace_session_tokens,
    rotate_refresh_row,
)
from app_user.repos.user_repo import update_user_disposition
from app_user.services.avatar_storage_service import upload_avatar
from app_user.utils.jwt_util import (
    access_expires_at_ms_from_token,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app_user.services.login_attempt_service import (
    bump_disposition_login_throttle,
    clear_on_success,
    record_failure,
)
from app_user.services.user_disposition_service import (
    LOGIN_FORBIDDEN_PUBLIC_MESSAGE,
    error_for_user_disposition,
)
from app_user.utils.user_serialization import user_to_public_dict
from app_user.services.verify_notice_service import (
    create_verify_event_and_send_notice,
    load_verify_notice_access_keys,
    post_verify_check,
    verify_payload_code_for_pending_event,
)
from app_verify.enums import ChannelEnum, VerifyLevelEnum
from common.utils.date_util import get_now_timestamp_ms
from common.consts.response_const import (
    RET_ACCOUNT_RESTRICTED,
    RET_DUPLICATE_REQUEST,
    RET_RATE_LIMITED,
    RET_TOKEN_REVOKED,
)
from common.exceptions.base_exception import CheckedException


class AuthService:
    @staticmethod
    def _lock_bruteforce(user, *, lk_count: int) -> None:
        window = settings.USER_LOGIN_FAIL_WINDOW_SECONDS
        max_lk = settings.USER_LOGIN_FAIL_MAX_ATTEMPTS_LOGIN_KEY
        reason = (
            "因登录失败达到阈值已自动锁定（禁止登录）："
            f"{window} 秒内同一账号失败 {lk_count} 次（阈值 {max_lk}）。"
        )
        with transaction.atomic(using="user_rw"):
            update_user_disposition(
                user.id,
                ctrl_status=UserDispositionEnum.LOGIN_FORBIDDEN.value,
                ctrl_reason=reason,
            )
            deprecate_all_tokens_for_user(user.id)

    @staticmethod
    def login(login_key: str, password: str, client_ip: str) -> dict:
        if not login_key or not password:
            raise ValueError("login_key and password are required")
        lk = login_key.strip()
        user = get_user_by_login(lk)
        if not user or user.status != UserStatusEnum.ENABLED.value:
            _, ip_c = record_failure(lk, client_ip)
            if ip_c >= settings.USER_LOGIN_FAIL_MAX_ATTEMPTS_IP:
                raise CheckedException(
                    detail="rate limit ip",
                    ret_code=RET_RATE_LIMITED,
                    message="尝试次数过多，请稍后再试。",
                    http_status=200,
                )
            raise ValueError("invalid username/email/phone or password")

        if not check_password(password, user.password_hash):
            lk_c, ip_c = record_failure(lk, client_ip)
            if lk_c >= settings.USER_LOGIN_FAIL_MAX_ATTEMPTS_LOGIN_KEY:
                AuthService._lock_bruteforce(user, lk_count=lk_c)
                raise CheckedException(
                    detail="bruteforce lock",
                    ret_code=RET_ACCOUNT_RESTRICTED,
                    message=LOGIN_FORBIDDEN_PUBLIC_MESSAGE,
                    http_status=200,
                )
            if ip_c >= settings.USER_LOGIN_FAIL_MAX_ATTEMPTS_IP:
                raise CheckedException(
                    detail="rate limit ip",
                    ret_code=RET_RATE_LIMITED,
                    message="尝试次数过多，请稍后再试。",
                    http_status=200,
                )
            raise ValueError("invalid username/email/phone or password")

        disp = error_for_user_disposition(user)
        if disp:
            n = bump_disposition_login_throttle(lk, client_ip)
            if n >= settings.USER_DISPOSITION_AUTH_THROTTLE_MAX:
                raise CheckedException(
                    detail="rate limit disposition auth",
                    ret_code=RET_RATE_LIMITED,
                    message="尝试次数过多，请稍后再试。",
                    http_status=200,
                )
            code, msg = disp
            raise CheckedException(
                detail="disposition",
                ret_code=code,
                message=msg,
                http_status=200,
            )

        clear_on_success(lk, client_ip)
        return AuthService._issue_session_tokens(user)

    @staticmethod
    def refresh(refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("invalid refresh token")
        user_id = payload.get("user_id")
        username = payload.get("username")
        if not user_id or not username:
            raise ValueError("invalid refresh token payload")

        user = get_user_by_id(user_id)
        if not user:
            raise ValueError("invalid refresh token")

        if not refresh_token_in_use(user_id=user_id, refresh_token=refresh_token):
            raise CheckedException(
                detail="refresh not in use",
                ret_code=RET_TOKEN_REVOKED,
                message="登录已失效，请重新登录。",
                http_status=200,
            )

        disp = error_for_user_disposition(user)
        if disp:
            code, msg = disp
            raise CheckedException(
                detail="disposition",
                ret_code=code,
                message=msg,
                http_status=200,
            )

        new_access = create_access_token(user_id=user_id, username=username)
        new_refresh = create_refresh_token(user_id=user_id, username=username)
        exp_ms = access_expires_at_ms_from_token(new_access)
        ok = rotate_refresh_row(
            user_id=user_id,
            old_refresh_token=refresh_token,
            new_access_token=new_access,
            new_refresh_token=new_refresh,
            access_expires_at_ms=exp_ms,
        )
        if not ok:
            raise CheckedException(
                detail="refresh rotate failed",
                ret_code=RET_TOKEN_REVOKED,
                message="登录已失效，请重新登录。",
                http_status=200,
            )
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
        }

    @staticmethod
    def request_password_reset_by_payload(payload: dict) -> dict:
        channel = (payload.get("notice_channel") or "").strip()
        target = (payload.get("notice_target") or "").strip()

        ttl_ms = int(settings.VERIFY_CODE_TTL_SECONDS) * 1000
        prior = get_latest_incomplete_event_by_notice(
            EventBizTypeEnum.PASSWORD_RESET.value,
            target,
        )
        if prior and get_now_timestamp_ms() - int(prior.ct) < ttl_ms:
            raise CheckedException(
                detail="password reset already pending for this notice target",
                ret_code=RET_DUPLICATE_REQUEST,
                message="该联系方式在验证码有效期内已发起过密码重置，请使用已发送的验证码或稍后再试。",
                data={"event_id": int(prior.id)},
                http_status=200,
            )

        return AuthService._request_password_reset(channel=channel, target=target)

    @staticmethod
    def _request_password_reset(channel: str, target: str) -> dict:
        notice_channel_label = channel.lower()
        if notice_channel_label not in {"email", "sms"}:
            raise ValueError("channel must be email or sms")
        target = target.strip()
        if not target:
            raise ValueError("target is required")

        notice_channel = ChannelEnum.from_label(notice_channel_label)
        user = (
            get_user_by_email(target)
            if notice_channel_label == "email"
            else get_user_by_phone(target)
        )
        if not user or user.status != UserStatusEnum.ENABLED.value:
            return {"sent": True}

        cancel_pending_events_by_notice(
            EventBizTypeEnum.PASSWORD_RESET.value,
            notice_channel,
            target,
        )
        pending_payload = {"user_id": user.id}
        event = create_verify_event_and_send_notice(
            biz_type=EventBizTypeEnum.PASSWORD_RESET.value,
            level=VerifyLevelEnum.HIGH.value,
            notice_channel=notice_channel,
            notice_target=target,
            payload_json=json.dumps(pending_payload, ensure_ascii=False),
            subject="Password reset verify code",
            content_template="Your password reset code is {code}. Event ID: {event_id}",
        )
        return {"sent": True, "event_id": event.id}

    @staticmethod
    def verify_password_reset_by_payload(payload: dict) -> dict:
        code = (payload.get("code") or "").strip()
        new_password = payload.get("new_password") or ""
        reset = AuthService._verify_password_reset(
            event_id=int(payload.get("event_id") or 0),
            code=code,
            new_password=new_password,
        )
        return {"reset": reset}

    @staticmethod
    def _verify_password_reset(
            *,
            event_id: int,
            code: str,
            new_password: str,
    ) -> bool:
        if event_id <= 0:
            raise ValueError("event_id is required")
        if not code:
            raise ValueError("code is required")
        if not new_password:
            raise ValueError("new_password is required")

        event = get_event_by_id(event_id)

        if (
                not event
                or event.biz_type != EventBizTypeEnum.PASSWORD_RESET
                or event.status != EventStatusEnum.PENDING_VERIFY.value
        ):
            raise ValueError("invalid or expired reset request")

        try:
            payload_data = json.loads(event.payload_json or "{}")
        except (TypeError, ValueError):
            payload_data = {}
        user_id = int(payload_data.get("user_id") or 0)
        if user_id <= 0:
            raise ValueError("invalid event payload")

        user = get_user_by_id(user_id)
        if not user or user.status != UserStatusEnum.ENABLED.value:
            raise ValueError("user not found or inactive")

        verify_access_key, _ = load_verify_notice_access_keys()
        verify_resp = post_verify_check(
            verify_access_key=verify_access_key,
            code_id=event.verify_code_id,
            code=code,
        )
        if not verify_resp or verify_resp.get("errorCode") != 0:
            raise ValueError("invalid or expired verify code")

        with transaction.atomic(using="user_rw"):
            update_user_password(user_id, make_password(new_password))
            deprecate_all_tokens_for_user(user_id)
            update_event_status(
                event.id,
                status=EventStatusEnum.COMPLETED.value,
                message="completed",
            )
        return True

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

        ttl_ms = int(settings.VERIFY_CODE_TTL_SECONDS) * 1000
        prior = get_latest_incomplete_event_by_notice(
            EventBizTypeEnum.REGISTER.value,
            notice_target,
        )
        if prior and get_now_timestamp_ms() - int(prior.ct) < ttl_ms:
            raise CheckedException(
                detail="register already pending for this notice target",
                ret_code=RET_DUPLICATE_REQUEST,
                message="该联系方式在验证码有效期内已发起过注册，请使用已发送的验证码或稍后再试。",
                data={"event_id": int(prior.id)},
                http_status=200,
            )

        avatar_url = upload_avatar(avatar) if avatar else ""
        pending_payload = {
            "username": username,
            "password_hash": make_password(password),
            "email": email,
            "phone": phone,
            "avatar": avatar_url,
            "ext": ext,
        }
        event = create_verify_event_and_send_notice(
            biz_type=EventBizTypeEnum.REGISTER,
            level=VerifyLevelEnum.HIGH.value,
            notice_channel=ChannelEnum.from_label(notice_channel),
            notice_target=notice_target,
            payload_json=json.dumps(pending_payload, ensure_ascii=False),
            subject="Register verify code",
            content_template="Your register verify code is {code}. Event ID: {event_id}",
        )
        return {"event_id": event.id}

    @staticmethod
    def register_verify_by_payload(payload: dict) -> dict:
        event, data = verify_payload_code_for_pending_event(
            payload=payload,
            expected_biz_type=EventBizTypeEnum.REGISTER,
        )
        with transaction.atomic(using="user_rw"):
            user = create_user(
                username=(data.get("username") or "").strip(),
                password_hash=data.get("password_hash") or "",
                email=(data.get("email") or "").strip(),
                phone=(data.get("phone") or "").strip(),
                avatar=data.get("avatar") or "",
                ext=data.get("ext") if isinstance(data.get("ext"), dict) else {},
            )
            user.status = UserStatusEnum.ENABLED.value
            user.save(using="user_rw", update_fields=["status"])
            update_event_status(
                event.id,
                status=EventStatusEnum.COMPLETED.value,
                message="completed",
            )
            return AuthService._issue_session_tokens(user)

    @staticmethod
    def _issue_session_tokens(user) -> dict:
        access = create_access_token(user_id=user.id, username=user.username)
        refresh = create_refresh_token(user_id=user.id, username=user.username)
        exp_ms = access_expires_at_ms_from_token(access)
        replace_session_tokens(
            user_id=user.id,
            access_token=access,
            refresh_token=refresh,
            access_expires_at_ms=exp_ms,
        )
        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": user_to_public_dict(user),
        }
