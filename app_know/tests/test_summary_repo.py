"""
Tests for summary repository (knowledge_summaries disabled).
Stubbed behavior: no Mongo, validation only.
"""
from unittest import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.repos.summary_repo import (
    save_summary,
    get_summary,
    list_summaries,
    delete_by_knowledge_id,
    search_summaries_by_text,
    SUMMARY_STORAGE_MAX_LEN,
    QUERY_SEARCH_MAX_LEN,
)


class SummaryRepoTest(TestCase):
    """Tests for summary repo (knowledge_summaries disabled - stubbed)."""

    def test_save_summary_returns_stub(self):
        """save_summary returns stub, does not persist."""
        out = save_summary(knowledge_id=1, summary="My summary", app_id=1)
        self.assertEqual(out["kid"], 1)
        self.assertEqual(out["summary"], "My summary")
        self.assertEqual(out["app_id"], 1)
        self.assertIsNone(out["id"])

    def test_save_summary_validation_invalid_knowledge_id(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=0, summary="x", app_id=1)
        self.assertIn("positive integer", str(ctx.exception))
        with self.assertRaises(ValueError):
            save_summary(knowledge_id=-1, summary="x", app_id=1)
        with self.assertRaises(ValueError):
            save_summary(knowledge_id=None, summary="x", app_id=1)

    def test_save_summary_validation_empty_app_id(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary="x", app_id=None)
        self.assertIn("app_id", str(ctx.exception))

    def test_save_summary_validation_summary_none(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary=None, app_id=1)
        self.assertIn("summary", str(ctx.exception))

    def test_save_summary_validation_summary_not_string(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary=123, app_id=1)
        self.assertIn("summary", str(ctx.exception))

    def test_save_summary_validation_summary_too_long(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(
                knowledge_id=1,
                summary="x" * (SUMMARY_STORAGE_MAX_LEN + 1),
                app_id=1,
            )
        self.assertIn("exceed", str(ctx.exception))

    def test_get_summary_always_none(self):
        """get_summary always returns None (no persistence)."""
        self.assertIsNone(get_summary(knowledge_id=1))
        self.assertIsNone(get_summary(knowledge_id=999, app_id=0))
        self.assertIsNone(get_summary(knowledge_id=2, app_id=1))

    def test_get_summary_invalid_knowledge_id_returns_none(self):
        self.assertIsNone(get_summary(knowledge_id=0))
        self.assertIsNone(get_summary(knowledge_id=-1))

    def test_list_summaries_always_empty(self):
        """list_summaries returns empty list."""
        items, total = list_summaries(app_id=1, offset=0, limit=10)
        self.assertEqual(total, 0)
        self.assertEqual(items, [])

    def test_list_summaries_validation(self):
        with self.assertRaises(ValueError):
            list_summaries(offset=-1, limit=10)
        with self.assertRaises(ValueError):
            list_summaries(offset=0, limit=0)
        with self.assertRaises(ValueError):
            list_summaries(offset=0, limit=LIMIT_LIST + 1)
        with self.assertRaises(ValueError) as ctx:
            list_summaries(offset=None, limit=10)
        self.assertIn("offset", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            list_summaries(offset=0, limit=None)
        self.assertIn("limit", str(ctx.exception))

    def test_delete_by_knowledge_id_always_zero(self):
        """delete_by_knowledge_id returns 0 (no persistence)."""
        n = delete_by_knowledge_id(knowledge_id=10)
        self.assertEqual(n, 0)

    def test_delete_by_knowledge_id_invalid_returns_zero(self):
        n = delete_by_knowledge_id(knowledge_id=0)
        self.assertEqual(n, 0)

    def test_search_summaries_by_text_always_empty(self):
        """search_summaries_by_text returns empty list."""
        items = search_summaries_by_text(query="keyword", limit=10)
        self.assertEqual(items, [])

    def test_search_summaries_by_text_validation(self):
        with self.assertRaises(ValueError) as ctx:
            search_summaries_by_text(query=None)
        self.assertIn("required", str(ctx.exception))
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="")
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="  ")
        with self.assertRaises(ValueError):
            search_summaries_by_text(query=123)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="x", limit=0)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="x", limit=LIMIT_LIST + 1)
        with self.assertRaises(ValueError) as ctx:
            search_summaries_by_text(
                query="x" * (QUERY_SEARCH_MAX_LEN + 1),
                limit=10,
            )
        self.assertIn("exceed", str(ctx.exception).lower())
