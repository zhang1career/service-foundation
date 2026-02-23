"""
Tests for summary service (generate, get, list, delete); validation and edge cases. Generated.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase

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

    @patch("app_know.services.summary_generator._get_text_ai")
    def test_generate_with_ai_success(self, mock_get_client):
        """generate_summary with use_ai=True uses TextAI client when available."""
        mock_client = MagicMock()
        mock_client.ask_and_answer.return_value = ("prompt", "AI generated summary for the knowledge.")
        mock_get_client.return_value = mock_client

        out = generate_summary(title="Test Title", description="Test Desc", use_ai=True)
        self.assertEqual(out, "AI generated summary for the knowledge.")
        mock_client.ask_and_answer.assert_called_once()

    @patch("app_know.services.summary_generator._get_text_ai")
    def test_generate_with_ai_fallback_on_failure(self, mock_get_client):
        """generate_summary falls back to rule-based when AI fails."""
        mock_client = MagicMock()
        mock_client.ask_and_answer.side_effect = RuntimeError("API error")
        mock_get_client.return_value = mock_client

        out = generate_summary(title="Test Title", description="Test Desc", use_ai=True)
        self.assertIn("Test Title", out)
        self.assertIn("Test Desc", out)

    @patch("app_know.services.summary_generator._get_text_ai")
    def test_generate_with_ai_fallback_when_client_none(self, mock_get_client):
        """generate_summary falls back to rule-based when TextAI client unavailable."""
        mock_get_client.return_value = None

        out = generate_summary(title="Test Title", use_ai=True)
        self.assertIn("Test Title", out)

    @patch("app_know.services.summary_generator._get_text_ai")
    def test_generate_with_ai_truncates_long_response(self, mock_get_client):
        """AI-generated summary is truncated if too long."""
        mock_client = MagicMock()
        mock_client.ask_and_answer.return_value = ("prompt", "x" * 3000)
        mock_get_client.return_value = mock_client

        out = generate_summary(title="T", max_length=100, use_ai=True)
        self.assertLessEqual(len(out), 100)
        self.assertTrue(out.endswith("..."))

    def test_generate_without_ai_uses_rule_based(self):
        """generate_summary with use_ai=False (default) uses rule-based."""
        out = generate_summary(title="Title", description="Desc", use_ai=False)
        self.assertIn("Title: Title", out)
        self.assertIn("Description: Desc", out)


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
        mock_entity.source_type = "doc"
        mock_get_know.return_value = mock_entity
        mock_save.return_value = {"knowledge_id": 1, "summary": "Title: Title Description: Desc", "app_id": 1}

        svc = SummaryService()
        out = svc.generate_and_save(knowledge_id=1, app_id=1)
        self.assertEqual(out["knowledge_id"], 1)
        mock_save.assert_called_once()
        call_kw = mock_save.call_args[1]
        self.assertEqual(call_kw["knowledge_id"], 1)
        self.assertEqual(call_kw["app_id"], 1)
        self.assertIn("Title", call_kw["summary"])

    def test_generate_and_save_validation_missing_app_id(self):
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=1, app_id="")
        self.assertIn("app_id", str(ctx.exception))

    def test_generate_and_save_validation_invalid_knowledge_id(self):
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.generate_and_save(knowledge_id=0, app_id=1)

    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_knowledge_not_found(self, mock_get_know):
        mock_get_know.return_value = None
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=99999, app_id=1)
        self.assertIn("not found", str(ctx.exception))

    @patch("app_know.services.summary_service.save_summary")
    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_empty_title_raises(self, mock_get_know, mock_save):
        mock_entity = MagicMock()
        mock_entity.title = ""
        mock_entity.description = None
        mock_get_know.return_value = mock_entity
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.generate_and_save(knowledge_id=1, app_id=1)
        self.assertIn("title", str(ctx.exception))
        mock_save.assert_not_called()

    def test_get_summary_validation(self):
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.get_summary(knowledge_id=0)

    def test_get_summary_validation_negative_id(self):
        """get_summary with negative knowledge_id raises ValueError (edge case)."""
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.get_summary(knowledge_id=-1)
        self.assertIn("positive", str(ctx.exception).lower())

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

    @patch("app_know.services.summary_service.repo_update_summary")
    def test_update_summary_success(self, mock_update):
        """update_summary calls repo and returns result."""
        mock_update.return_value = {
            "knowledge_id": 1,
            "app_id": 1,
            "summary": "Updated summary",
        }
        svc = SummaryService()
        out = svc.update_summary(knowledge_id=1, app_id=1, summary="Updated summary")
        self.assertEqual(out["summary"], "Updated summary")
        mock_update.assert_called_once_with(
            knowledge_id=1, app_id=1, summary="Updated summary", source=None
        )

    def test_update_summary_validation_missing_app_id(self):
        """update_summary raises ValueError when app_id is missing."""
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_summary(knowledge_id=1, app_id="")
        self.assertIn("app_id", str(ctx.exception))

    def test_update_summary_validation_invalid_knowledge_id(self):
        """update_summary raises ValueError when knowledge_id is invalid."""
        svc = SummaryService()
        with self.assertRaises(ValueError):
            svc.update_summary(knowledge_id=0, app_id=1)

    @patch("app_know.services.summary_service.repo_update_summary")
    def test_update_summary_not_found(self, mock_update):
        """update_summary raises ValueError when summary not found."""
        mock_update.return_value = None
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_summary(knowledge_id=999, app_id=1, summary="Updated")
        self.assertIn("not found", str(ctx.exception))

    @patch("app_know.services.summary_service.delete_mapping_by_knowledge_id")
    @patch("app_know.services.summary_service.repo_delete_summary")
    def test_delete_summary_success(self, mock_delete, mock_del_mapping):
        """delete_summary calls repo and returns True on success."""
        mock_delete.return_value = True
        svc = SummaryService()
        result = svc.delete_summary(knowledge_id=1, app_id=1)
        self.assertTrue(result)
        mock_delete.assert_called_once_with(knowledge_id=1, app_id=1)
        mock_del_mapping.assert_called_once_with(knowledge_id=1, app_id=1)

    def test_delete_summary_validation_missing_app_id(self):
        """delete_summary raises ValueError when app_id is missing."""
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.delete_summary(knowledge_id=1, app_id="")
        self.assertIn("app_id", str(ctx.exception))

    @patch("app_know.services.summary_service.delete_mapping_by_knowledge_id")
    @patch("app_know.services.summary_service.repo_delete_summary")
    def test_delete_summary_not_found(self, mock_delete, mock_del_mapping):
        """delete_summary raises ValueError when summary not found."""
        mock_delete.return_value = False
        svc = SummaryService()
        with self.assertRaises(ValueError) as ctx:
            svc.delete_summary(knowledge_id=999, app_id=1)
        self.assertIn("not found", str(ctx.exception))

    @patch("app_know.services.summary_service.create_or_update_mapping")
    @patch("app_know.services.summary_service.save_summary")
    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_creates_mapping(self, mock_get_know, mock_save, mock_mapping):
        """generate_and_save creates MySQL mapping after saving summary."""
        mock_entity = MagicMock()
        mock_entity.title = "Title"
        mock_entity.description = "Desc"
        mock_entity.source_type = "doc"
        mock_get_know.return_value = mock_entity
        mock_save.return_value = {
            "id": "65a1b2c3d4e5f6",
            "knowledge_id": 1,
            "summary": "S",
            "app_id": 1,
        }

        svc = SummaryService()
        svc.generate_and_save(knowledge_id=1, app_id=1)
        mock_mapping.assert_called_once_with(
            knowledge_id=1, app_id=1, summary_id="65a1b2c3d4e5f6"
        )

    @patch("app_know.services.summary_generator._get_text_ai")
    @patch("app_know.services.summary_service.save_summary")
    @patch("app_know.services.summary_service.get_knowledge_by_id")
    def test_generate_and_save_with_ai(self, mock_get_know, mock_save, mock_text_ai):
        """generate_and_save with use_ai=True sets source to ai_generated."""
        mock_entity = MagicMock()
        mock_entity.title = "Title"
        mock_entity.description = "Desc"
        mock_entity.source_type = "doc"
        mock_get_know.return_value = mock_entity
        mock_client = MagicMock()
        mock_client.ask_and_answer.return_value = ("prompt", "AI summary")
        mock_text_ai.return_value = mock_client
        mock_save.return_value = {"knowledge_id": 1, "summary": "AI summary", "app_id": 1}

        svc = SummaryService()
        svc.generate_and_save(knowledge_id=1, app_id=1, use_ai=True)
        call_kw = mock_save.call_args[1]
        self.assertEqual(call_kw["source"], "ai_generated")
