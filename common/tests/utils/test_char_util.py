from unittest import TestCase


class TestCharUtil(TestCase):

    def test_replace_char(self):
        # lazy load
        from common.utils.char_util import replace_char

        # Test case 1: Basic replacement
        raw_string = "hello world"
        replace_dict = {"h": "H", "w": "W", " ": ""}
        expected_result = "HelloWorld"
        acutal_result = replace_char(raw_string, replace_dict)
        self.assertEqual(expected_result, acutal_result)

        # Test case 2: No replacements
        raw_string = "hello world"
        replace_dict = {}
        expected_result = "hello world"
        acutal_result = replace_char(raw_string, replace_dict)
        self.assertEqual(expected_result, acutal_result)

        # Test case 3: All characters replaced
        raw_string = "abc"
        replace_dict = {"a": "A", "b": "B", "c": "C"}
        expected_result = "ABC"
        acutal_result = replace_char(raw_string, replace_dict)
        self.assertEqual(expected_result, acutal_result)

        # Test case 4: Mixed characters
        raw_string = "abc123"
        replace_dict = {"a": "A", "1": "one"}
        expected_result = "Abcone23"
        acutal_result = replace_char(raw_string, replace_dict)
        self.assertEqual(expected_result, acutal_result)
