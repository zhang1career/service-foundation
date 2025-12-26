from unittest import TestCase

from common.services.text.text_helper import TextHelper


class TestTextHelper(TestCase):
    def setUp(self):
        self.dut = TextHelper()

    def test_find_most_similar_str(self):
        text_list = ["启用", "不启用"]
        match_text = "不启用"
        actual_result = self.dut.find_most_similar_str(text_list, match_text)
        print(actual_result)
