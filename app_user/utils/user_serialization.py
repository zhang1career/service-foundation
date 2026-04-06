import json


def _user_payload(
    user,
    *,
    ctrl_reason: str,
) -> dict:
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
        "auth_status": user.auth_status or 0,
        "ctrl_status": user.ctrl_status,
        "ctrl_reason": ctrl_reason,
        "ext": ext_data,
        "ct": user.ct,
        "ut": user.ut,
    }


def user_to_public_dict(user) -> dict:
    """对外 API：不返回内部处置说明。"""
    return _user_payload(user, ctrl_reason="")


def user_to_console_dict(user) -> dict:
    """控制台：可展示完整 ctrl_reason。"""
    return _user_payload(user, ctrl_reason=(user.ctrl_reason or "").strip())
