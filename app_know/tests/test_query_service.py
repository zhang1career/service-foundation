"""
Tests for logical query service (Atlas + Neo4j combined ranking). Generated.
Round 2: skills-scoped query test (app_id=skills uses Neo4j pipeline).
"""
from unittest import TestCase
from unittest.mock import patch, MagicMock

from common.consts.query_const import LIMIT_LIST

from app_know.repos.summary_repo import QUERY_SEARCH_MAX_LEN
from app_know.services.query_service import (
    LogicalQueryService,
    DEFAULT_QUERY_LIMIT,
    _validate_query,
    _validate_limit,
)


class ValidateQueryTest(TestCase):
    """Tests for _validate_query."""

    def test_requires_non_empty_string(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_query(None)
        self.assertIn("required", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            _validate_query("")
        self.assertIn("empty", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            _validate_query("   ")
        self.assertIn("empty", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            _validate_query(123)
        self.assertIn("string", str(ctx.exception))

    def test_accepts_non_empty_string(self):
        self.assertEqual(_validate_query("hello"), "hello")
        self.assertEqual(_validate_query("  bar  "), "bar")

    def test_query_too_long_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_query("x" * (QUERY_SEARCH_MAX_LEN + 1))
        self.assertIn("exceed", str(ctx.exception).lower())

    def test_query_max_length_accepted(self):
        self.assertEqual(
            _validate_query("x" * QUERY_SEARCH_MAX_LEN),
            "x" * QUERY_SEARCH_MAX_LEN,
        )


class ValidateLimitTest(TestCase):
    """Tests for _validate_limit."""

    def test_none_returns_default(self):
        self.assertEqual(_validate_limit(None), DEFAULT_QUERY_LIMIT)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_limit("10")
        self.assertIn("integer", str(ctx.exception))
        with self.assertRaises(ValueError):
            _validate_limit(0)
        with self.assertRaises(ValueError):
            _validate_limit(-1)
        with self.assertRaises(ValueError):
            _validate_limit(LIMIT_LIST + 1)

    def test_valid_returns_value(self):
        self.assertEqual(_validate_limit(10), 10)
        self.assertEqual(_validate_limit(1), 1)
        self.assertEqual(_validate_limit(LIMIT_LIST), LIMIT_LIST)


class LogicalQueryServiceTest(TestCase):
    """Tests for LogicalQueryService.query with mocked Atlas and Neo4j."""

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_only_returns_ranked(self, mock_search, mock_related):
        mock_search.return_value = [
            {"knowledge_id": 1, "summary": "First hit", "score": 1.0},
            {"knowledge_id": 2, "summary": "Second", "score": 1.0},
        ]
        mock_related.return_value = []
        svc = LogicalQueryService()
        out = svc.query(query="test", app_id=None, limit=10)
        self.assertIn("data", out)
        self.assertEqual(len(out["data"]), 2)
        self.assertEqual(out["data"][0]["knowledge_id"], 1)
        self.assertEqual(out["data"][0]["source"], "atlas")
        self.assertEqual(out["data"][0]["hop"], 0)
        mock_search.assert_called_once()
        mock_related.assert_not_called()

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_with_app_id_calls_neo4j(self, mock_search, mock_related):
        mock_search.return_value = [{"knowledge_id": 1, "summary": "Hit", "score": 1.0}]
        mock_related.return_value = [
            {"type": "knowledge", "knowledge_id": 2, "source_knowledge_id": 1, "hop": 1},
        ]
        svc = LogicalQueryService()
        out = svc.query(query="test", app_id="myapp", limit=10)
        self.assertIn("data", out)
        self.assertGreaterEqual(len(out["data"]), 1)
        mock_related.assert_called_once()
        call_kw = mock_related.call_args[1]
        self.assertEqual(call_kw["app_id"], "myapp")
        self.assertEqual(call_kw["knowledge_ids"], [1])

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_skills_app_id_uses_neo4j_pipeline(self, mock_search, mock_related):
        """Skills-scoped query (app_id=skills) uses Atlas summary relevance + Neo4j graph reasoning."""
        mock_search.return_value = [{"knowledge_id": 1, "summary": "Python skill", "score": 1.0}]
        mock_related.return_value = [
            {"type": "entity", "entity_type": "skill", "entity_id": "s1", "source_knowledge_id": 1, "hop": 1},
        ]
        svc = LogicalQueryService()
        out = svc.query(query="programming", app_id="skills", limit=20)
        self.assertIn("data", out)
        self.assertGreaterEqual(len(out["data"]), 1)
        mock_search.assert_called_once_with(query="programming", app_id="skills", limit=20)
        mock_related.assert_called_once()
        call_kw = mock_related.call_args[1]
        self.assertEqual(call_kw["app_id"], "skills")
        self.assertEqual(call_kw["knowledge_ids"], [1])

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_combined_ranking(self, mock_search, mock_related):
        mock_search.return_value = [{"knowledge_id": 1, "summary": "A", "score": 1.0}]
        mock_related.return_value = [
            {"type": "entity", "entity_type": "task", "entity_id": "e1", "source_knowledge_id": 1, "hop": 1},
        ]
        svc = LogicalQueryService()
        out = svc.query(query="test", app_id="app1", limit=10)
        data = out["data"]
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["type"], "knowledge")
        self.assertEqual(data[0]["knowledge_id"], 1)
        if len(data) > 1:
            self.assertEqual(data[1]["type"], "entity")
            self.assertEqual(data[1]["entity_type"], "task")

    def test_query_validation(self):
        svc = LogicalQueryService()
        with self.assertRaises(ValueError) as ctx:
            svc.query(query="", app_id=None)
        self.assertIn("empty", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            svc.query(query=None, app_id=None)
        self.assertIn("required", str(ctx.exception))
        with self.assertRaises(ValueError):
            svc.query(query="x", limit=0)
        with self.assertRaises(ValueError):
            svc.query(query="x", limit=LIMIT_LIST + 1)

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_empty_returns_empty(self, mock_search, mock_related):
        mock_search.return_value = []
        mock_related.return_value = []
        svc = LogicalQueryService()
        out = svc.query(query="nonexistent", app_id=None, limit=10)
        self.assertEqual(out["data"], [])
        self.assertEqual(out["total_num"], 0)
        mock_search.assert_called_once()
        mock_related.assert_not_called()

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_and_neo4j_both_empty(self, mock_search, mock_related):
        mock_search.return_value = []
        mock_related.return_value = []
        svc = LogicalQueryService()
        out = svc.query(query="x", app_id="myapp", limit=10)
        self.assertEqual(out["data"], [])
        self.assertEqual(out["total_num"], 0)

    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_raises_propagates(self, mock_search):
        mock_search.side_effect = RuntimeError("Atlas connection failed")
        svc = LogicalQueryService()
        with self.assertRaises(RuntimeError):
            svc.query(query="test", app_id=None, limit=10)

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_neo4j_raises_propagates(self, mock_search, mock_related):
        mock_search.return_value = [{"knowledge_id": 1, "summary": "Hit", "score": 1.0}]
        mock_related.side_effect = OSError("Neo4j error")
        svc = LogicalQueryService()
        with self.assertRaises(OSError):
            svc.query(query="test", app_id="myapp", limit=10)

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_value_error_from_atlas_propagates(self, mock_search, mock_related):
        mock_search.side_effect = ValueError("query cannot be empty")
        svc = LogicalQueryService()
        with self.assertRaises(ValueError):
            svc.query(query="", app_id=None, limit=10)

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_result_missing_knowledge_id_skipped(self, mock_search, mock_related):
        """Atlas result items without knowledge_id are skipped (edge case)."""
        mock_search.return_value = [
            {"knowledge_id": 1, "summary": "Hit", "score": 1.0},
            {"summary": "No id", "score": 1.0},
            {"knowledge_id": None, "summary": "None id", "score": 1.0},
        ]
        mock_related.return_value = []
        svc = LogicalQueryService()
        out = svc.query(query="test", app_id=None, limit=10)
        self.assertEqual(len(out["data"]), 1)
        self.assertEqual(out["data"][0]["knowledge_id"], 1)
        self.assertEqual(out["data"][0]["source"], "atlas")

    @patch("app_know.services.query_service.get_related_by_knowledge_ids")
    @patch("app_know.services.query_service.search_summaries_by_text")
    def test_query_atlas_empty_and_neo4j_has_related_returns_neo4j_only(self, mock_search, mock_related):
        """When Atlas returns empty, Neo4j still returns related if app_id set (edge case)."""
        mock_search.return_value = []
        mock_related.return_value = [
            {"type": "knowledge", "knowledge_id": 5, "source_knowledge_id": 1, "hop": 1},
        ]
        svc = LogicalQueryService()
        out = svc.query(query="x", app_id="myapp", limit=10)
        self.assertEqual(len(out["data"]), 1)
        self.assertEqual(out["data"][0]["knowledge_id"], 5)
        self.assertEqual(out["data"][0]["source"], "neo4j")
