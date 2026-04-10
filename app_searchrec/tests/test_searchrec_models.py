from django.test import SimpleTestCase

from app_searchrec.enums import SearchRecEventType


class TestSearchRecEventType(SimpleTestCase):
    def test_integer_values(self):
        self.assertEqual(SearchRecEventType.UNKNOWN, 0)
        self.assertEqual(SearchRecEventType.SEARCH_QUERY, 1)
        self.assertEqual(SearchRecEventType.IMPRESSION, 2)
        self.assertEqual(SearchRecEventType.CLICK, 3)
        self.assertEqual(SearchRecEventType.UPSERT, 4)
