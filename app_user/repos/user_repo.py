import json
from typing import Optional, Sequence

from app_user.enums import UserDispositionEnum, UserStatusEnum
from app_user.models import User
from common.utils.date_util import get_now_timestamp_ms
from common.utils.db_exception_util import normalize_optional_contact


def get_user_by_id(user_id: int) -> Optional[User]:
    return User.objects.using("user_rw").filter(id=user_id).first()


def get_user_by_username(username: str) -> Optional[User]:
    return User.objects.using("user_rw").filter(username=username).first()


def get_user_by_email(email: str) -> Optional[User]:
    return User.objects.using("user_rw").filter(email=email).first()


def get_user_by_phone(phone: str) -> Optional[User]:
    return User.objects.using("user_rw").filter(phone=phone).first()


def get_user_by_login(login_key: str) -> Optional[User]:
    return (
        User.objects.using("user_rw")
        .filter(username=login_key)
        .first()
        or User.objects.using("user_rw").filter(email=login_key).first()
        or User.objects.using("user_rw").filter(phone=login_key).first()
    )


def create_user(
    username: str,
    password_hash: str,
    email: str | None = None,
    phone: str | None = None,
    avatar: str = "",
    ext: Optional[dict] = None,
) -> User:
    now_ms = get_now_timestamp_ms()
    ext_json = json.dumps(ext or {}, ensure_ascii=False)
    return User.objects.using("user_rw").create(
        username=username,
        password_hash=password_hash,
        email=normalize_optional_contact(email),
        phone=normalize_optional_contact(phone),
        avatar=avatar,
        status=UserStatusEnum.DISABLED.value,
        auth_status=0,
        ext=ext_json,
        ct=now_ms,
        ut=now_ms,
    )


def update_user_profile(user_id: int, email: Optional[str], phone: Optional[str], avatar: Optional[str], ext: Optional[dict]) -> Optional[User]:
    user = get_user_by_id(user_id)
    if not user:
        return None
    update_fields = []
    if email is not None:
        user.email = normalize_optional_contact(email)
        update_fields.append("email")
    if phone is not None:
        user.phone = normalize_optional_contact(phone)
        update_fields.append("phone")
    if avatar is not None:
        user.avatar = avatar
        update_fields.append("avatar")
    if ext is not None:
        user.ext = json.dumps(ext or {}, ensure_ascii=False)
        update_fields.append("ext")
    if update_fields:
        user.ut = get_now_timestamp_ms()
        update_fields.append("ut")
        user.save(using="user_rw", update_fields=update_fields)
    return user


def update_user_password(user_id: int, password_hash: str) -> bool:
    user = get_user_by_id(user_id)
    if not user:
        return False
    user.password_hash = password_hash
    user.ut = get_now_timestamp_ms()
    user.save(using="user_rw", update_fields=["password_hash", "ut"])
    return True


def list_users(offset: int, limit: int, user_ids: Optional[Sequence[int]] = None):
    query = User.objects.using("user_rw").all()
    if user_ids is not None:
        query = query.filter(id__in=list(user_ids))
    total = query.count()
    data = list(query.order_by("-ct")[offset:offset + limit])
    return data, total


def update_user_status(user_id: int, status: int) -> Optional[User]:
    user = get_user_by_id(user_id)
    if not user:
        return None
    user.status = status
    user.ut = get_now_timestamp_ms()
    user.save(using="user_rw", update_fields=["status", "ut"])
    return user


def update_user_auth_status(user_id: int, auth_status: int) -> Optional[User]:
    user = get_user_by_id(user_id)
    if not user:
        return None
    user.auth_status = int(auth_status or 0)
    user.ut = get_now_timestamp_ms()
    user.save(using="user_rw", update_fields=["auth_status", "ut"])
    return user


def update_user_disposition(
        user_id: int,
        *,
        ctrl_status: int,
        ctrl_reason: str,
) -> Optional[User]:
    user = get_user_by_id(user_id)
    if not user:
        return None
    user.ctrl_status = int(ctrl_status)
    user.ctrl_reason = ctrl_reason or ""
    user.ut = get_now_timestamp_ms()
    user.save(
        using="user_rw",
        update_fields=["ctrl_status", "ctrl_reason", "ut"],
    )
    return user


def clear_user_disposition(user_id: int) -> Optional[User]:
    user = get_user_by_id(user_id)
    if not user:
        return None
    user.ctrl_status = UserDispositionEnum.NONE.value
    user.ctrl_reason = ""
    user.ut = get_now_timestamp_ms()
    user.save(
        using="user_rw",
        update_fields=["ctrl_status", "ctrl_reason", "ut"],
    )
    return user
