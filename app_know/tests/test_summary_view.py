"""
Tests for knowledge summary API views (validation, error handling, edge cases). Generated.
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_OK,
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
)

from app_know.views.summary_view import (
    KnowledgeSummaryView,
    KnowledgeSummaryListView,
)


class KnowledgeSummaryViewTest(TestCase):
    """Tests for GET/POST knowledge/<id>/summary (fully mocked, no DB required)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.entity_id = 1

    @patch("app_know.views.summary_view.SummaryService")
    def test_post_generate_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.generate_and_save.return_value = {
            "knowledge_id": self.entity_id,
            "summary": "Title: Summary Test Description: Desc",
            "app_id": "myapp",
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": "myapp"},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["app_id"], "myapp")
        mock_svc.generate_and_save.assert_called_once_with(
            knowledge_id=self.entity_id, app_id="myapp", use_ai=False
        )

    def test_post_missing_app_id(self):
        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_post_invalid_entity_id(self):
        request = self.factory.post(
            "/api/know/knowledge/0/summary",
            data={"app_id": "myapp"},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_invalid_entity_id_non_integer(self):
        request = self.factory.get("/api/know/knowledge/abc/summary")
        response = KnowledgeSummaryView.as_view()(request, entity_id="abc")
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_invalid_entity_id_empty(self):
        request = self.factory.get("/api/know/knowledge//summary")
        response = KnowledgeSummaryView.as_view()(request, entity_id="")
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    @patch("app_know.views.summary_view.SummaryService")
    def test_get_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.get_summary.return_value = {
            "knowledge_id": self.entity_id,
            "summary": "A summary",
            "app_id": "myapp",
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get(f"/api/know/knowledge/{self.entity_id}/summary")
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["summary"], "A summary")

    @patch("app_know.views.summary_view.SummaryService")
    def test_get_not_found(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.get_summary.return_value = None
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get(f"/api/know/knowledge/{self.entity_id}/summary")
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_know.views.summary_view.SummaryService")
    def test_post_app_id_coerced_from_number(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.generate_and_save.return_value = {
            "knowledge_id": self.entity_id,
            "summary": "S",
            "app_id": "42",
        }
        mock_svc_cls.return_value = mock_svc
        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": 42},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        mock_svc.generate_and_save.assert_called_once_with(
            knowledge_id=self.entity_id, app_id="42", use_ai=False
        )

    @patch("app_know.views.summary_view.SummaryService")
    def test_post_invalid_json_returns_parse_error(self, mock_svc_cls):
        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data='{"app_id": "x"',
            content_type="application/json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    def test_post_app_id_whitespace_only_returns_validation_error(self):
        """POST with app_id only whitespace returns RET_MISSING_PARAM."""
        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": "   \t  "},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)


class KnowledgeSummaryListViewTest(TestCase):
    """Tests for GET knowledge/summaries."""

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_know.views.summary_view.SummaryService")
    def test_list_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.list_summaries.return_value = {
            "data": [{"knowledge_id": 1, "summary": "S1", "app_id": "a"}],
            "total_num": 1,
            "next_offset": None,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get("/api/know/knowledge/summaries", {"limit": 10, "offset": 0})
        response = KnowledgeSummaryListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 1)
        self.assertEqual(len(data["data"]["data"]), 1)

    def test_list_validation_invalid_limit(self):
        request = self.factory.get("/api/know/knowledge/summaries", {"limit": -1})
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    def test_list_validation_limit_zero(self):
        request = self.factory.get("/api/know/knowledge/summaries", {"limit": 0})
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    def test_list_validation_offset_negative(self):
        request = self.factory.get("/api/know/knowledge/summaries", {"offset": -1})
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    def test_list_validation_limit_over_max(self):
        request = self.factory.get(
            "/api/know/knowledge/summaries", {"limit": LIMIT_LIST + 1}
        )
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)

    @patch("app_know.views.summary_view.SummaryService")
    def test_list_invalid_knowledge_id_ignored_filter(self, mock_svc_cls):
        """List with non-integer knowledge_id treats filter as omitted (no crash)."""
        mock_svc = MagicMock()
        mock_svc.list_summaries.return_value = {
            "data": [],
            "total_num": 0,
            "next_offset": None,
        }
        mock_svc_cls.return_value = mock_svc
        request = self.factory.get(
            "/api/know/knowledge/summaries",
            {"knowledge_id": "not_a_number", "limit": "10", "offset": "0"},
        )
        response = KnowledgeSummaryListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        mock_svc.list_summaries.assert_called_once()
        call_kw = mock_svc.list_summaries.call_args[1]
        self.assertIsNone(call_kw["knowledge_id"])

    def test_list_offset_non_integer_returns_validation_error(self):
        """List with offset that cannot be parsed as integer returns validation error."""
        request = self.factory.get(
            "/api/know/knowledge/summaries",
            {"offset": "abc", "limit": "10"},
        )
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_list_limit_non_integer_returns_validation_error(self):
        """List with limit that cannot be parsed as integer returns validation error."""
        request = self.factory.get(
            "/api/know/knowledge/summaries",
            {"offset": "0", "limit": "xyz"},
        )
        response = KnowledgeSummaryListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)


class KnowledgeSummaryViewMockedTest(TestCase):
    """Tests for PUT/DELETE summary endpoints (fully mocked, no DB required)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.entity_id = 1

    @patch("app_know.views.summary_view.SummaryService")
    def test_post_with_use_ai_flag(self, mock_svc_cls):
        """POST with use_ai=True passes flag to service."""
        mock_svc = MagicMock()
        mock_svc.generate_and_save.return_value = {
            "kid": self.entity_id,
            "summary": "AI Generated Summary",
            "app_id": "myapp",
        }
        mock_svc_cls.return_value = mock_svc
        request = self.factory.post(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": "myapp", "use_ai": True},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        mock_svc.generate_and_save.assert_called_once_with(
            knowledge_id=self.entity_id, app_id="myapp", use_ai=True
        )

    @patch("app_know.views.summary_view.SummaryService")
    def test_put_update_success(self, mock_svc_cls):
        """PUT updates summary successfully."""
        mock_svc = MagicMock()
        mock_svc.update_summary.return_value = {
            "knowledge_id": self.entity_id,
            "summary": "Updated summary",
            "app_id": "myapp",
        }
        mock_svc_cls.return_value = mock_svc
        request = self.factory.put(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": "myapp", "summary": "Updated summary"},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["summary"], "Updated summary")

    def test_put_missing_app_id_returns_validation_error(self):
        """PUT with missing app_id returns RET_MISSING_PARAM."""
        request = self.factory.put(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"summary": "Updated"},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.summary_view.SummaryService")
    def test_put_not_found(self, mock_svc_cls):
        """PUT for non-existent summary returns RET_RESOURCE_NOT_FOUND."""
        mock_svc = MagicMock()
        mock_svc.update_summary.side_effect = ValueError("not found")
        mock_svc_cls.return_value = mock_svc
        request = self.factory.put(
            f"/api/know/knowledge/{self.entity_id}/summary",
            data={"app_id": "myapp", "summary": "Updated"},
            format="json",
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_know.views.summary_view.SummaryService")
    def test_delete_success(self, mock_svc_cls):
        """DELETE summary successfully."""
        mock_svc = MagicMock()
        mock_svc.delete_summary.return_value = True
        mock_svc_cls.return_value = mock_svc
        request = self.factory.delete(
            f"/api/know/knowledge/{self.entity_id}/summary?app_id=myapp"
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)

    def test_delete_missing_app_id_returns_validation_error(self):
        """DELETE with missing app_id returns RET_MISSING_PARAM."""
        request = self.factory.delete(
            f"/api/know/knowledge/{self.entity_id}/summary"
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.summary_view.SummaryService")
    def test_delete_not_found(self, mock_svc_cls):
        """DELETE non-existent summary returns RET_RESOURCE_NOT_FOUND."""
        mock_svc = MagicMock()
        mock_svc.delete_summary.side_effect = ValueError("not found")
        mock_svc_cls.return_value = mock_svc
        request = self.factory.delete(
            f"/api/know/knowledge/{self.entity_id}/summary?app_id=myapp"
        )
        response = KnowledgeSummaryView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)
