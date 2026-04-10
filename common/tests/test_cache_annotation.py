"""Tests for common.annotation.cache decorators."""
from django.core.cache import caches
from django.test import override_settings

from common.annotation.cache import django_cached, local_ttl_cached


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cache-annotation-test",
        }
    }
)
def test_django_cached_uses_second_call_from_cache():
    caches["default"].clear()

    calls = {"n": 0}

    @django_cached(key_prefix="t", ttl_seconds=60)
    def f(x: int) -> int:
        calls["n"] += 1
        return x * 2

    assert f(3) == 6
    assert f(3) == 6
    assert calls["n"] == 1


def test_local_ttl_cached_second_call_hits_memory():
    calls = {"n": 0}

    @local_ttl_cached(maxsize=8, ttl_seconds=300.0)
    def g(x: int) -> int:
        calls["n"] += 1
        return x + 1

    assert g(1) == 2
    assert g(1) == 2
    assert calls["n"] == 1


