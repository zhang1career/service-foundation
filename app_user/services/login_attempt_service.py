import hashlib

from django.conf import settings
from django.core.cache import cache

_CACHE_PREFIX_LK = "lf:lk:"
_CACHE_PREFIX_IP = "lf:ip:"
_CACHE_PREFIX_DISP = "lf:disp:"


def _bump(key: str, window: int) -> int:
    if cache.add(key, 1, timeout=window):
        return 1
    return cache.incr(key)


def record_failure(login_key: str, client_ip: str) -> tuple[int, int]:
    window = settings.USER_LOGIN_FAIL_WINDOW_SECONDS
    lk_key = f"{_CACHE_PREFIX_LK}{login_key}"
    ip_key = f"{_CACHE_PREFIX_IP}{client_ip}"
    lk_count = _bump(lk_key, window)
    ip_count = _bump(ip_key, window)
    return lk_count, ip_count


def clear_on_success(login_key: str, client_ip: str) -> None:
    cache.delete_many(
        [
            f"{_CACHE_PREFIX_LK}{login_key}",
            f"{_CACHE_PREFIX_IP}{client_ip}",
            _disposition_throttle_cache_key(login_key, client_ip),
        ],
    )


def _disposition_throttle_cache_key(login_key: str, client_ip: str) -> str:
    digest = hashlib.sha256(f"{login_key}\0{client_ip}".encode()).hexdigest()
    return f"{_CACHE_PREFIX_DISP}{digest}"


def bump_disposition_login_throttle(login_key: str, client_ip: str) -> int:
    """
    Successful password but user blocked by disposition: count attempts per (login_key, ip).
    Independent from wrong-password counters (record_failure).
    """
    window = settings.USER_DISPOSITION_AUTH_THROTTLE_WINDOW_SECONDS
    key = _disposition_throttle_cache_key(login_key, client_ip)
    return _bump(key, window)
