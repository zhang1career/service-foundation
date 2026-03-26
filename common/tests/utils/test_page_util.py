from unittest import TestCase

from common.utils.page_util import build_page


class TestPageUtil(TestCase):
    def test_build_page(self):
        data = [{"id": 1}, {"id": 2}]
        result = build_page(data_list=data, next_offset=2, total_num=10)
        self.assertEqual(result["data"], data)
        self.assertEqual(result["next_offset"], 2)
        self.assertEqual(result["total_num"], 10)
