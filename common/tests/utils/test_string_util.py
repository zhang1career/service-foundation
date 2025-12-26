from unittest import TestCase


class Test(TestCase):
    def test_explode(self):
        # lazy load
        from common.utils.string_util import explode

        # normal case
        origin_str = "a,b,c"
        expected_result = ["a", "b", "c"]
        actual_result = explode(origin_str)
        self.assertEqual(expected_result, actual_result)

        # empty case
        origin_str = ""
        expected_result = []
        actual_result = explode(origin_str)
        self.assertEqual(expected_result, actual_result)

        # None case
        origin_str = None
        expected_result = []
        actual_result = explode(origin_str)
        self.assertEqual(expected_result, actual_result)

    def test_check_blank(self):
        # lazy load
        from common.utils.string_util import check_blank

        # normal case
        origin_str = "a"
        expected_result = False
        actual_result = check_blank(origin_str)
        self.assertEqual(expected_result, actual_result)

        # empty case
        origin_str = ""
        expected_result = True
        actual_result = check_blank(origin_str)
        self.assertEqual(expected_result, actual_result)

        # None case
        origin_str = None
        expected_result = True
        actual_result = check_blank(origin_str)
        self.assertEqual(expected_result, actual_result)

        # blank case
        origin_str = " "
        expected_result = True
        actual_result = check_blank(origin_str)
        self.assertEqual(expected_result, actual_result)

    def test_downcase_only_if_first_char_is_uppercase(self):
        # lazy load
        from common.utils.string_util import downcase_only_if_first_char_is_uppercase

        origin_str = "Abc"
        expected_str = "abc"
        expected_bool = False
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "def"
        expected_str = "def"
        expected_bool = False
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "XYZ"
        expected_str = "XYZ"
        expected_bool = True
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "p"
        expected_str = "p"
        expected_bool = False
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "Q"
        expected_str = "Q"
        expected_bool = True
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = ""
        expected_str = None
        expected_bool = None
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "rEt"
        expected_str = "rEt"
        expected_bool = False
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)

        origin_str = "rET"
        expected_str = "rET"
        expected_bool = False
        actual_str, actual_bool = downcase_only_if_first_char_is_uppercase(origin_str)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_bool, actual_bool)