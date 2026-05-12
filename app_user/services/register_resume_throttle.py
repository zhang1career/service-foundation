"""Rate limits for ``POST /register/request`` (resume after ``no_verify``)."""

from django.conf import settings
from django.core.cache import cache

_PREFIX_IP = "reg:resume:ip:"
_PREFIX_UID = "reg:resume:uid:"


def _bump(key: str, window: int) -> int:
    if cache.add(key, 1, timeout=window):
        return 1
    return cache.incr(key)


def register_resume_ip_count(client_ip: str) -> int:
    window = int(settings.USER_REGISTER_RESUME_IP_WINDOW_SECONDS)
    return _bump(f"{_PREFIX_IP}{client_ip}", window)


def register_resume_user_count(user_id: int) -> int:
    window = int(settings.USER_REGISTER_RESUME_USER_WINDOW_SECONDS)
    return _bump(f"{_PREFIX_UID}{int(user_id)}", window)
