"""
Tests for Knowledge REST API views (CRUD endpoints).
Generated.
"""
import json
import time
from unittest.mock import patch

from django.db import transaction, connections
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

from app_know.models import Knowledge
from app_know.views.knowledge_view import KnowledgeListView, KnowledgeDetailView


class KnowledgeListViewTest(TestCase):
    databases = {"default", "know_rw"}

    def setUp(self):
        self.factory = APIRequestFactory()
        Knowledge.objects.using("know_rw").all().delete()

    def tearDown(self):
        try:
            Knowledge.objects.using("know_rw").all().delete()
        except Exception:
            conn = connections["know_rw"]
            if conn.in_atomic_block:
                transaction.set_rollback(True, using="know_rw")

    def test_list_empty(self):
        request = self.factory.get("/api/know/knowledge")
        response = KnowledgeListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 0)
        self.assertEqual(data["data"]["data"], [])

    def test_create_success(self):
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

    def test_list_with_params(self):
        Knowledge.objects.using("know_rw").create(
            title="A", source_type="doc",
            ct=int(time.time() * 1000), ut=int(time.time() * 1000),
        )
        Knowledge.objects.using("know_rw").create(
            title="B", source_type="url",
            ct=int(time.time() * 1000), ut=int(time.time() * 1000),
        )
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

    def test_create_with_metadata_dict(self):
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

    def test_create_with_description_as_number_coerced_to_string(self):
        """Create knowledge with description as number is coerced to string (edge case)."""
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
    databases = {"default", "know_rw"}

    def setUp(self):
        self.factory = APIRequestFactory()
        Knowledge.objects.using("know_rw").all().delete()
        self.entity = Knowledge.objects.using("know_rw").create(
            title="Detail Test",
            description="D",
            source_type="doc",
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000),
        )
        self.entity_id = self.entity.id

    def tearDown(self):
        try:
            Knowledge.objects.using("know_rw").all().delete()
        except Exception:
            conn = connections["know_rw"]
            if conn.in_atomic_block:
                transaction.set_rollback(True, using="know_rw")

    def test_get_success(self):
        request = self.factory.get(f"/api/know/knowledge/{self.entity_id}")
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["id"], self.entity_id)
        self.assertEqual(data["data"]["title"], "Detail Test")

    def test_get_not_found(self):
        request = self.factory.get("/api/know/knowledge/99999")
        response = KnowledgeDetailView.as_view()(request, entity_id=99999)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    def test_put_success(self):
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

    @patch("app_know.services.summary_service.delete_by_knowledge_id")
    def test_delete_success(self, mock_delete_summaries):
        """Delete knowledge entity; Atlas/summary_repo mocked so no real DNS or connection. Generated."""
        mock_delete_summaries.return_value = 0
        request = self.factory.delete(f"/api/know/knowledge/{self.entity_id}")
        response = KnowledgeDetailView.as_view()(request, entity_id=self.entity_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIsNone(
            Knowledge.objects.using("know_rw").filter(id=self.entity_id).first()
        )
        mock_delete_summaries.assert_called_once_with(knowledge_id=self.entity_id)

    def test_delete_not_found(self):
        request = self.factory.delete("/api/know/knowledge/99999")
        response = KnowledgeDetailView.as_view()(request, entity_id=99999)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    def test_put_empty_title_validation(self):
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
