"""Cache generation and query key behavior (locmem)."""

from django.core.cache import caches
from django.test import TestCase, override_settings


@override_settings(
    CONFIG_CACHE_TTL_SECONDS=300,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
        "config": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
)
class TestConfigCacheService(TestCase):
    def setUp(self):
        caches["config"].clear()

    def test_bump_changes_generation(self):
        from app_config.services.config_cache_service import (
            bump_config_cache_generation,
            get_rid_generation,
        )

        self.assertEqual(get_rid_generation(5), 0)
        bump_config_cache_generation(5)
        self.assertEqual(get_rid_generation(5), 1)
        bump_config_cache_generation(5)
        self.assertEqual(get_rid_generation(5), 2)

    def test_query_cache_miss_after_bump(self):
        from app_config.services.config_cache_service import (
            bump_config_cache_generation,
            get_rid_generation,
            query_cache_get,
            query_cache_set,
        )

        rid = 3
        gen0 = get_rid_generation(rid)
        query_cache_set(rid, gen0, "key", "h1", {"value": 1})
        self.assertEqual(query_cache_get(rid, gen0, "key", "h1"), {"value": 1})
        bump_config_cache_generation(rid)
        gen1 = get_rid_generation(rid)
        self.assertIsNone(query_cache_get(rid, gen1, "key", "h1"))

    def test_query_cache_set_respects_ttl_setting(self):
        from django.test import override_settings

        from app_config.services.config_cache_service import (
            get_rid_generation,
            query_cache_get,
            query_cache_set,
        )

        with override_settings(CONFIG_CACHE_TTL_SECONDS=60):
            rid = 9
            gen0 = get_rid_generation(rid)
            query_cache_set(rid, gen0, "k2", "hh", {"v": 2})
            self.assertEqual(query_cache_get(rid, gen0, "k2", "hh"), {"v": 2})
