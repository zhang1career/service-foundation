"""Tests for KeepconDeviceType."""

from django.test import SimpleTestCase

from app_keepcon.enums.device_type_enum import KeepconDeviceType


class TestKeepconDeviceType(SimpleTestCase):
    def test_values(self):
        self.assertEqual(KeepconDeviceType.values(), [1, 2, 3])

    def test_is_valid(self):
        self.assertTrue(KeepconDeviceType.is_valid(1))
        self.assertFalse(KeepconDeviceType.is_valid(0))
        self.assertFalse(KeepconDeviceType.is_valid(99))

    def test_normalize_int(self):
        self.assertEqual(KeepconDeviceType.normalize(1), 1)
        self.assertEqual(KeepconDeviceType.normalize(2), 2)

    def test_normalize_int_invalid_raises(self):
        with self.assertRaises(ValueError) as ctx:
            KeepconDeviceType.normalize(99)
        self.assertIn("device_type", str(ctx.exception).lower())

    def test_normalize_legacy_strings(self):
        self.assertEqual(KeepconDeviceType.normalize("mobile"), 1)
        self.assertEqual(KeepconDeviceType.normalize("  WEB "), 2)
        self.assertEqual(KeepconDeviceType.normalize("iot"), 3)

    def test_normalize_digit_string(self):
        self.assertEqual(KeepconDeviceType.normalize("2"), 2)

    def test_normalize_enum_member(self):
        self.assertEqual(KeepconDeviceType.normalize(KeepconDeviceType.IOT), 3)

    def test_normalize_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            KeepconDeviceType.normalize("watch")
