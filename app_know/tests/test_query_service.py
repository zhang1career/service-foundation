from unittest import TestCase
from unittest.mock import patch

from app_know.services.query_service import (
    QUERY_SEARCH_MAX_LEN,
    DEFAULT_QUERY_LIMIT,
    LogicalQueryService,
    validate_limit,
    validate_query,
)
from common.consts.query_const import LIMIT_LIST


class ValidateQueryTest(TestCase):
    def test_validate_query(self):
        self.assertEqual(validate_query(" hello "), "hello")
        with self.assertRaises(ValueError):
            validate_query(None)
        with self.assertRaises(ValueError):
            validate_query("")
        with self.assertRaises(ValueError):
            validate_query("x" * (QUERY_SEARCH_MAX_LEN + 1))


class ValidateLimitTest(TestCase):
    def test_validate_limit(self):
        self.assertEqual(validate_limit(None), DEFAULT_QUERY_LIMIT)
        self.assertEqual(validate_limit(1), 1)
        self.assertEqual(validate_limit(LIMIT_LIST), LIMIT_LIST)
        with self.assertRaises(ValueError):
            validate_limit(0)
        with self.assertRaises(ValueError):
            validate_limit(LIMIT_LIST + 1)


class LogicalQueryServiceTest(TestCase):
    @patch("app_know.services.query_service._search_graphiti")
    def test_query_list_format(self, mock_search):
        mock_search.return_value = [{"knowledge_id": 11, "content": "foo", "score": 0.9, "group_id": "g1"}]
        out = LogicalQueryService().query(query="foo", app_id=7, limit=10)
        self.assertEqual(out["total_num"], 1)
        self.assertEqual(out["data"][0]["source"], "graphiti")
        mock_search.assert_called_once_with(query="foo", batch_id=7, limit=10)

    @patch("app_know.services.query_service._search_graphiti")
    def test_query_triple_format(self, mock_search):
        mock_search.return_value = [{"knowledge_id": 12, "content": "bar", "score": 0.8, "group_id": "g2"}]
        out = LogicalQueryService().query(query="bar", output_format="triple")
        self.assertEqual(out["total_triples"], 1)
        self.assertEqual(out["triples"][0]["predicate"], "retrieved")
