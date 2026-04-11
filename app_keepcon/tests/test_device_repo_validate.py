"""Tests for device_repo key validation (no database)."""

from django.test import SimpleTestCase

from app_keepcon.repos.device_repo import validate_device_key


class TestValidateDeviceKey(SimpleTestCase):
    def test_accepts_word_chars_dot_dash(self):
        self.assertEqual(validate_device_key("phone-001"), "phone-001")
        self.assertEqual(validate_device_key("a.b_1"), "a.b_1")

    def test_strips_whitespace(self):
        self.assertEqual(validate_device_key("  k1  "), "k1")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_device_key("")
        with self.assertRaises(ValueError):
            validate_device_key("   ")

    def test_rejects_invalid_chars(self):
        with self.assertRaises(ValueError):
            validate_device_key("bad key")
