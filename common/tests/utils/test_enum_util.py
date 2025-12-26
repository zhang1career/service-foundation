from unittest import TestCase


class EnumUtilTest(TestCase):
    def test_enum_contains(self):
        # lazy load
        from common.utils.enum_util import enum_contains
        from common.tests.enums.test_enum import TestEnum
        # normal case
        result = enum_contains(TestEnum, "a")
        self.assertTrue(result)
        # not in case
        result = enum_contains(TestEnum, "d")
        self.assertFalse(result)
        # empty case
        result = enum_contains(TestEnum, "")
        self.assertFalse(result)

    def test_enum_item_by_name(self):
        # lazy load
        from common.utils.enum_util import enum_item_by_name
        from common.tests.enums.test_enum import TestEnum
        # normal case
        result = enum_item_by_name(TestEnum, "a")
        self.assertEqual(result, TestEnum.a)
        # not in case
        result = enum_item_by_name(TestEnum, "d")
        self.assertIsNone(result)
        # empty case
        result = enum_item_by_name(TestEnum, "")
        self.assertIsNone(result)
