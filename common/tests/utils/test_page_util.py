from unittest import TestCase

from common.utils.page_util import build_page, slice_window_for_page


class TestPageUtil(TestCase):
    def test_build_page(self):
        data = [{"id": 1}, {"id": 2}]
        result = build_page(data_list=data, next_offset=2, total_num=10)
        self.assertEqual(result["data"], data)
        self.assertEqual(result["next_offset"], 2)
        self.assertEqual(result["total_num"], 10)

    def test_slice_window_for_page_basic(self):
        offset, resolved_page, total_pages = slice_window_for_page(total=95, page=2, page_size=10)
        self.assertEqual(offset, 10)
        self.assertEqual(resolved_page, 2)
        self.assertEqual(total_pages, 10)

    def test_slice_window_for_page_clamps_page(self):
        offset, resolved_page, total_pages = slice_window_for_page(total=15, page=99, page_size=10)
        self.assertEqual(offset, 10)
        self.assertEqual(resolved_page, 2)
        self.assertEqual(total_pages, 2)

    def test_slice_window_for_page_empty_total(self):
        offset, resolved_page, total_pages = slice_window_for_page(total=0, page=5, page_size=10)
        self.assertEqual(offset, 0)
        self.assertEqual(resolved_page, 1)
        self.assertEqual(total_pages, 1)

    def test_slice_window_for_page_invalid_page_size(self):
        offset, resolved_page, total_pages = slice_window_for_page(total=3, page=2, page_size=0)
        self.assertEqual(offset, 1)
        self.assertEqual(resolved_page, 2)
        self.assertEqual(total_pages, 3)
