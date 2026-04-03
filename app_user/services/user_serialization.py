import json


def user_to_public_dict(user) -> dict:
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
