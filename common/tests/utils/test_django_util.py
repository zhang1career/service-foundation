from django.http import QueryDict
from django.test import SimpleTestCase, override_settings

from common.utils.django_util import effective_setting_str, post_like_mapping_to_dict


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


class PostLikeMappingToDictTests(SimpleTestCase):
    def test_querydict_uses_last_value_per_key(self):
        q = QueryDict("a=1&a=2&b=x")
        self.assertEqual(post_like_mapping_to_dict(q), {"a": "2", "b": "x"})

    def test_plain_dict_copied(self):
        d = {"k": 1}
        out = post_like_mapping_to_dict(d)
        self.assertEqual(out, d)
        out["k"] = 2
        self.assertEqual(d["k"], 1)

    def test_mapping_like_accepted(self):
        class M:
            def keys(self):
                return ["a"]

            def __getitem__(self, k):
                return "v"

        self.assertEqual(post_like_mapping_to_dict(M()), {"a": "v"})
