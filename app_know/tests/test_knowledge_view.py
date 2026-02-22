"""
Tests for Knowledge REST API views (CRUD endpoints).
Generated.
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

from app_know.views.knowledge_view import KnowledgeListView, KnowledgeDetailView


class KnowledgeListViewTest(TestCase):
    """Tests for KnowledgeListView (fully mocked, no DB required)."""

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_list_empty(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.list_knowledge.return_value = {"total_num": 0, "data": []}
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get("/api/know/knowledge")
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 0)
        self.assertEqual(data["data"]["data"], [])

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_create_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.create_knowledge.return_value = {
            "id": 1,
            "title": "API Title",
            "description": "Desc",
            "source_type": "doc",
            "metadata": None,
            "ct": 1700000000000,
            "ut": 1700000000000,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.post(
            "/api/know/knowledge",
            data={"title": "API Title", "description": "Desc", "source_type": "doc"},
            format="json",
        )
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIn("id", data["data"])
        self.assertEqual(data["data"]["title"], "API Title")

    def test_create_missing_title(self):
        request = self.factory.post(
            "/api/know/knowledge",
            data={"description": "Only desc"},
            format="json",
        )
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_list_with_params(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.list_knowledge.return_value = {
            "total_num": 1,
            "data": [{"id": 1, "title": "A", "source_type": "doc"}],
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get(
            "/api/know/knowledge",
            {"offset": 0, "limit": 10, "source_type": "doc"},
        )
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 1)
        self.assertEqual(len(data["data"]["data"]), 1)
        self.assertEqual(data["data"]["data"][0]["source_type"], "doc")

    def test_list_validation_invalid_offset(self):
        request = self.factory.get("/api/know/knowledge", {"offset": -1})
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_list_validation_invalid_limit(self):
        request = self.factory.get("/api/know/knowledge", {"limit": 0})
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_create_with_metadata_dict(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.create_knowledge.return_value = {
            "id": 1,
            "title": "With Meta",
            "description": None,
            "source_type": None,
            "metadata": '{"key": "value", "n": 1}',
            "ct": 1700000000000,
            "ut": 1700000000000,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.post(
            "/api/know/knowledge",
            data={"title": "With Meta", "metadata": {"key": "value", "n": 1}},
            format="json",
        )
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIn("metadata", data["data"])
        self.assertEqual(data["data"]["metadata"], '{"key": "value", "n": 1}')

    def test_list_limit_over_max_returns_validation_error(self):
        request = self.factory.get(
            "/api/know/knowledge",
            {"offset": 0, "limit": LIMIT_LIST + 1},
        )
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_list_offset_non_numeric_returns_validation_error(self):
        request = self.factory.get("/api/know/knowledge", {"offset": "x"})
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_create_empty_title_whitespace_returns_validation_error(self):
        request = self.factory.post(
            "/api/know/knowledge",
            data={"title": "   ", "source_type": "doc"},
            format="json",
        )
        response = KnowledgeListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_create_with_description_as_number_coerced_to_string(self, mock_svc_cls):
        """Create knowledge with description as number is coerced to string (edge case)."""
        mock_svc = MagicMock()
        mock_svc.create_knowledge.return_value = {
            "id": 1,
            "title": "Num Desc",
            "description": "12345",
            "source_type": "doc",
            "metadata": None,
            "ct": 1700000000000,
            "ut": 1700000000000,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.post(
            "/api/know/knowledge",
            data={"title": "Num Desc", "description": 12345, "source_type": "doc"},
            format="json",
        )
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIn("id", data["data"])
        self.assertEqual(data["data"]["description"], "12345")


class KnowledgeDetailViewTest(TestCase):
    """Tests for KnowledgeDetailView (fully mocked, no DB required)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.entity_id = 1

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_get_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.get_knowledge.return_value = {
            "id": self.entity_id,
            "title": "Detail Test",
            "description": "D",
            "source_type": "doc",
            "metadata": None,
            "ct": 1700000000000,
            "ut": 1700000000000,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get(f"/api/know/knowledge/{self.entity_id}")
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["id"], self.entity_id)
        self.assertEqual(data["data"]["title"], "Detail Test")

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_get_not_found(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.get_knowledge.side_effect = ValueError("Knowledge 99999 not found")
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get("/api/know/knowledge/99999")
        response = KnowledgeDetailView.as_view()(request, entity_id=99999)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_put_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.update_knowledge.return_value = {
            "id": self.entity_id,
            "title": "Updated Title",
            "description": "D",
            "source_type": "doc",
            "metadata": None,
            "ct": 1700000000000,
            "ut": 1700000000001,
        }
        mock_svc_cls.return_value = mock_svc

        request = self.factory.put(
            f"/api/know/knowledge/{self.entity_id}",
            data={"title": "Updated Title"},
            format="json",
        )
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["title"], "Updated Title")

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_delete_success(self, mock_svc_cls):
        """Delete knowledge entity; service fully mocked."""
        mock_svc = MagicMock()
        mock_svc.delete_knowledge.return_value = True
        mock_svc_cls.return_value = mock_svc

        request = self.factory.delete(f"/api/know/knowledge/{self.entity_id}")
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        mock_svc.delete_knowledge.assert_called_once_with(self.entity_id)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_delete_not_found(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.delete_knowledge.side_effect = ValueError("Knowledge 99999 not found")
        mock_svc_cls.return_value = mock_svc

        request = self.factory.delete("/api/know/knowledge/99999")
        response = KnowledgeDetailView.as_view()(request, entity_id=99999)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_know.views.knowledge_view.KnowledgeService")
    def test_put_empty_title_validation(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.update_knowledge.side_effect = ValueError("title cannot be empty")
        mock_svc_cls.return_value = mock_svc

        request = self.factory.put(
            f"/api/know/knowledge/{self.entity_id}",
            data={"title": "   "},
            format="json",
        )
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_get_entity_id_zero_returns_invalid_param(self):
        request = self.factory.get("/api/know/knowledge/0")
        response = KnowledgeDetailView.as_view()(request, entity_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_put_entity_id_zero_returns_invalid_param(self):
        request = self.factory.put(
            "/api/know/knowledge/0",
            data={"title": "Updated"},
            format="json",
        )
        response = KnowledgeDetailView.as_view()(request, entity_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_delete_entity_id_zero_returns_invalid_param(self):
        request = self.factory.delete("/api/know/knowledge/0")
        response = KnowledgeDetailView.as_view()(request, entity_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_entity_id_negative_returns_invalid_param(self):
        """Detail view rejects negative entity_id (input validation)."""
        request = self.factory.get("/api/know/knowledge/-1")
        response = KnowledgeDetailView.as_view()(request, entity_id=-1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_put_entity_id_negative_returns_invalid_param(self):
        """PUT with negative entity_id returns invalid param."""
        request = self.factory.put(
            "/api/know/knowledge/-1",
            data={"title": "Updated"},
            format="json",
        )
        response = KnowledgeDetailView.as_view()(request, entity_id=-1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_delete_entity_id_negative_returns_invalid_param(self):
        """DELETE with negative entity_id returns invalid param (input validation)."""
        request = self.factory.delete("/api/know/knowledge/-1")
        response = KnowledgeDetailView.as_view()(request, entity_id=-1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)
