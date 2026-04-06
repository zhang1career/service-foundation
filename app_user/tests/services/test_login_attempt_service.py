"""Login counter behavior (isolated cache backend)."""

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from app_user.services.login_attempt_service import (
    bump_disposition_login_throttle,
    clear_on_success,
    record_failure,
)

_LOC_MEM = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "login-attempt-test",
    }
}


@override_settings(CACHES=_LOC_MEM)
class TestLoginAttemptService(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_record_failure_increments_login_key_and_ip(self):
        lk, ip = record_failure("alice", "10.0.0.1")
        self.assertEqual(lk, 1)
        self.assertEqual(ip, 1)
        lk2, ip2 = record_failure("alice", "10.0.0.1")
        self.assertEqual(lk2, 2)
        self.assertEqual(ip2, 2)

    def test_record_failure_tracks_login_key_and_ip_separately(self):
        record_failure("bob", "10.0.0.1")
        lk, ip = record_failure("bob", "10.0.0.2")
        self.assertEqual(lk, 2)
        self.assertEqual(ip, 1)

    def test_clear_on_success_clears_both_counters(self):
        record_failure("carol", "192.168.1.1")
        record_failure("carol", "192.168.1.1")
        clear_on_success("carol", "192.168.1.1")
        lk, ip = record_failure("carol", "192.168.1.1")
        self.assertEqual(lk, 1)
        self.assertEqual(ip, 1)

    def test_bump_disposition_throttle_is_per_login_key_and_ip(self):
        self.assertEqual(bump_disposition_login_throttle("alice", "10.0.0.1"), 1)
        self.assertEqual(bump_disposition_login_throttle("alice", "10.0.0.1"), 2)
        self.assertEqual(bump_disposition_login_throttle("bob", "10.0.0.1"), 1)

    def test_clear_on_success_clears_disposition_throttle(self):
        bump_disposition_login_throttle("dave", "10.0.0.2")
        bump_disposition_login_throttle("dave", "10.0.0.2")
        clear_on_success("dave", "10.0.0.2")
        self.assertEqual(bump_disposition_login_throttle("dave", "10.0.0.2"), 1)
