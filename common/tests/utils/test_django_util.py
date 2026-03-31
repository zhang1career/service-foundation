from django.test import SimpleTestCase, override_settings

from common.utils.django_util import effective_setting_str


class EffectiveSettingStrTests(SimpleTestCase):
    @override_settings(DJANGO_UTIL_EFFECTIVE_TEST="from_settings")
    def test_none_uses_settings(self):
        self.assertEqual(effective_setting_str(None, "DJANGO_UTIL_EFFECTIVE_TEST"), "from_settings")

    @override_settings(DJANGO_UTIL_EFFECTIVE_TEST="from_settings")
    def test_whitespace_override_falls_back_to_settings(self):
        self.assertEqual(effective_setting_str("  \t  ", "DJANGO_UTIL_EFFECTIVE_TEST"), "from_settings")

    @override_settings(DJANGO_UTIL_EFFECTIVE_TEST="from_settings")
    def test_non_empty_override_wins(self):
        self.assertEqual(
            effective_setting_str("  explicit  ", "DJANGO_UTIL_EFFECTIVE_TEST"),
            "explicit",
        )

    @override_settings(DJANGO_UTIL_EFFECTIVE_TEST="from_settings")
    def test_numeric_override_coerced_to_str(self):
        self.assertEqual(effective_setting_str(42, "DJANGO_UTIL_EFFECTIVE_TEST"), "42")

    def test_missing_setting_returns_empty(self):
        self.assertEqual(effective_setting_str(None, "DJANGO_UTIL_EFFECTIVE_MISSING_XYZ"), "")
