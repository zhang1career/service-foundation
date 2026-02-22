"""
Tests for summary service (generate, get, list, delete); validation and edge cases. Generated.
"""
from unittest import TestCase
from unittest.mock import patch, MagicMock

from common.consts.query_const import LIMIT_LIST

from app_know.services.summary_service import SummaryService
from app_know.services.summary_generator import generate_summary


class SummaryGeneratorTest(TestCase):
    """Tests for summary generator."""

    def test_generate_basic(self):
        out = generate_summary(title="Hello", description="World")
        self.assertIn("Hello", out)
        self.assertIn("World", out)

    def test_generate_requires_title(self):
        with self.assertRaises(ValueError):
            generate_summary(title="")
        with self.assertRaises(ValueError):
            generate_summary(title="  ")
        with self.assertRaises(ValueError) as ctx:
            generate_summary(title=None)
        self.assertIn("title", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            generate_summary(title=123)
        self.assertIn("string", str(ctx.exception))

    def test_generate_validates_max_length(self):
        with self.assertRaises(ValueError) as ctx:
            generate_summary(title="T", max_length=0)
        self.assertIn("max_length", str(ctx.exception))
        with self.assertRaises(ValueError):
            generate_summary(title="T", max_length=-1)
        with self.assertRaises(ValueError):
            generate_summary(title="T", max_length=None)

    def test_generate_truncates_long(self):
        long_desc = "x" * 3000
        out = generate_summary(title="T", description=long_desc, max_length=100)
        self.assertLessEqual(len(out), 103)
        self.assertTrue(out.endswith("...") or len(out) <= 100)


class SummaryServiceTest(TestCase):
    """Tests for SummaryService with mocked repo and knowledge."""

    @patch("app_know.services.summary_service.repo_list_summaries")
    @patch("app_know.services.summary_service.repo_get_summary")
    @patch("app_know.services.summary_service.save_summary")
    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_success(self, mock_get_know, mock_save, mock_get_summary, mock_list):
        mock_entity = MagicMock()
        mock_entity.title = "Title"
        mock_entity.description = "Desc"
        mock_entity.metadata = None
        mock_entity.source_type = "doc"
        mock_get_know.return_value = mock_entity
        mock_save.return_value = {"knowledge_id": 1, "summary": "Title: Title Description: Desc", "app_id": "app1"}

        svc = SummaryService()
        out = svc.generate_and_save(knowledge_id=1, app_id="app1")
        self.assertEqual(out["knowledge_id"], 1)
        mock_save.assert_called_once()
        call_kw = mock_save.call_args[1]
        self.assertEqual(call_kw["knowledge_id"], 1)
        self.assertEqual(call_kw["app_id"], "app1")
        self.assertIn("Title", call_kw["summary"])

    def test_generate_and_save_validation_missing_app_id(self):
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=1, app_id="")
        self.assertIn("app_id", str(ctx.exception))

    def test_generate_and_save_validation_invalid_knowledge_id(self):
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.generate_and_save(knowledge_id=0, app_id="app1")

    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_knowledge_not_found(self, mock_get_know):
        mock_get_know.return_value = None
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=99999, app_id="app1")
        self.assertIn("not found", str(ctx.exception))

    @patch("app_know.services.summary_service.save_summary")
    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_empty_title_raises(self, mock_get_know, mock_save):
        mock_entity = MagicMock()
        mock_entity.title = ""
        mock_entity.description = None
        mock_entity.metadata = None
        mock_get_know.return_value = mock_entity
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=1, app_id="app1")
        self.assertIn("title", str(ctx.exception))
        mock_save.assert_not_called()

    def test_get_summary_validation(self):
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.get_summary(knowledge_id=0)

    @patch("app_know.services.summary_service.repo_list_summaries")
    def test_list_summaries_validation(self, mock_list):
        mock_list.return_value = ([], 0)
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.list_summaries(offset=-1, limit=10)
        with self.assertRaises(ValueError):
            svc.list_summaries(offset=0, limit=LIMIT_LIST + 1)
        with self.assertRaises(ValueError):
            svc.list_summaries(offset=0, limit=0)
        with self.assertRaises(ValueError) as ctx:
            svc.list_summaries(offset="x", limit=10)
        self.assertIn("offset", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            svc.list_summaries(offset=0, limit="y")
        self.assertIn("limit", str(ctx.exception))

    @patch("app_know.services.summary_service.repo_list_summaries")
    def test_list_summaries_defaults_offset_limit(self, mock_list):
        mock_list.return_value = ([], 0)
        svc = SummaryService()
        svc.list_summaries()
        mock_list.assert_called_once()
        call_kw = mock_list.call_args[1]
        self.assertEqual(call_kw["offset"], 0)
        self.assertEqual(call_kw["limit"], 100)

    @patch("app_know.services.summary_service.repo_list_summaries")
    def test_list_summaries_success(self, mock_list):
        mock_list.return_value = ([{"knowledge_id": 1, "summary": "S1"}], 1)
        svc = SummaryService()
        out = svc.list_summaries(offset=0, limit=10)
        self.assertEqual(out["total_num"], 1)
        self.assertEqual(len(out["data"]), 1)
        self.assertIsNone(out["next_offset"])

    @patch("app_know.services.summary_service.delete_by_knowledge_id")
    def test_delete_summaries_for_knowledge(self, mock_del):
        mock_del.return_value = 2
        svc = SummaryService()
        n = svc.delete_summaries_for_knowledge(knowledge_id=1)
        self.assertEqual(n, 2)
        mock_del.assert_called_once_with(knowledge_id=1)

    def test_delete_summaries_invalid_id_returns_zero(self):
        svc = SummaryService()
        n = svc.delete_summaries_for_knowledge(knowledge_id=0)
        self.assertEqual(n, 0)
