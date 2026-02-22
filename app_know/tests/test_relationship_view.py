"""
Tests for relationship REST API views (create/update/query, validation, and error handling).
RelationshipService is mocked so no real Neo4j connection is used. Generated.
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient

from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_OK,
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_RESOURCE_NOT_FOUND,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
)

from app_know.views.relationship_view import (
    RelationshipListView,
    RelationshipDetailView,
)


class RelationshipListViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_query_missing_app_id_returns_validation_error(self):
        request = self.factory.get("/api/know/knowledge/relationships")
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_query_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.query_relationships.return_value = {
            "data": [],
            "total_num": 0,
            "next_offset": None,
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": 10, "offset": 0},
        )
        response = RelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 0)
        self.assertEqual(data["data"]["data"], [])

    def test_create_missing_app_id_returns_validation_error(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_create_invalid_relationship_type_returns_invalid_param(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "invalid_type",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_create_knowledge_entity_missing_entity_type_returns_validation_error(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_create_knowledge_knowledge_missing_target_returns_validation_error(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_knowledge",
                "source_knowledge_id": 1,
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_create_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.create_relationship.return_value = {
            "relationship_id": 1,
            "app_id": "myapp",
            "relationship_type": "knowledge_entity",
            "source_knowledge_id": 1,
            "entity_type": "user",
            "entity_id": "e1",
            "properties": {},
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["relationship_type"], "knowledge_entity")
        self.assertEqual(data["data"]["entity_id"], "e1")

    def test_query_invalid_limit_or_offset_returns_validation_error(self):
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": "x", "offset": 0},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_query_invalid_offset_returns_validation_error(self):
        """GET with non-integer offset returns RET_INVALID_PARAM; no service call so no Neo4j. Generated."""
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": "10", "offset": "y"},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_query_limit_zero_returns_invalid_param(self):
        """GET with limit=0 returns RET_INVALID_PARAM; validation before service. Generated."""
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": "0", "offset": "0"},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_query_negative_offset_returns_invalid_param(self):
        """GET with offset=-1 returns RET_INVALID_PARAM; validation before service. Generated."""
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": "10", "offset": "-1"},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_post_empty_body_treated_as_empty_dict(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data=None,
            content_type="application/json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_post_service_raises_non_value_error_returns_db_error(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.create_relationship.side_effect = RuntimeError("Neo4j connection failed")
        mock_service_cls.return_value = mock_service
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_DB_ERROR)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_create_with_predicate_success(self, mock_service_cls):
        """POST with predicate field creates relationship with predicate."""
        mock_service = MagicMock()
        mock_service.create_relationship.return_value = {
            "relationship_id": 1,
            "app_id": "myapp",
            "relationship_type": "knowledge_entity",
            "source_knowledge_id": 1,
            "entity_type": "user",
            "entity_id": "e1",
            "predicate": "belongs_to",
            "properties": {},
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
                "predicate": "belongs_to",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["predicate"], "belongs_to")

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_query_with_predicate_filter(self, mock_service_cls):
        """GET with predicate filter passes it to service."""
        mock_service = MagicMock()
        mock_service.query_relationships.return_value = {
            "data": [],
            "total_num": 0,
            "next_offset": None,
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "predicate": "belongs_to"},
        )
        response = RelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.query_relationships.assert_called_once()
        call_kw = mock_service.query_relationships.call_args[1]
        self.assertEqual(call_kw["predicate"], "belongs_to")

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_query_with_format_triple(self, mock_service_cls):
        """GET with format=triple calls query_relationships_as_triples.
        Note: DRF intercepts 'format' for content negotiation, so we use a subclass
        that overrides perform_content_negotiation to avoid 404.
        """
        from rest_framework.renderers import JSONRenderer

        mock_service = MagicMock()
        mock_service.query_relationships_as_triples.return_value = {
            "data": [
                {
                    "subject": {"node_type": "knowledge", "knowledge_id": 1},
                    "predicate": "relates_to",
                    "object": {"node_type": "entity", "entity_type": "user", "entity_id": "e1"},
                    "relationship_id": 42,
                    "properties": {},
                }
            ],
            "total_num": 1,
            "next_offset": None,
        }
        mock_service_cls.return_value = mock_service

        class TestRelationshipListView(RelationshipListView):
            def perform_content_negotiation(self, request, force=False):
                return (JSONRenderer(), "application/json")

        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "format": "triple"},
        )
        response = TestRelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        mock_service.query_relationships_as_triples.assert_called_once()
        self.assertIn("subject", data["data"]["data"][0])
        self.assertIn("predicate", data["data"]["data"][0])
        self.assertIn("object", data["data"]["data"][0])


class RelationshipDetailViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_missing_app_id_returns_validation_error(self):
        request = self.factory.get("/api/know/knowledge/relationships/1")
        response = RelationshipDetailView.as_view()(
            request, relationship_id=1
        )
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_get_not_found(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.get_relationship.return_value = None
        mock_service_cls.return_value = mock_service
        request = self.factory.get(
            "/api/know/knowledge/relationships/999",
            {"app_id": "myapp"},
        )
        response = RelationshipDetailView.as_view()(
            request, relationship_id=999
        )
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_get_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.get_relationship.return_value = {
            "relationship_id": 1,
            "app_id": "myapp",
            "properties": {"k": "v"},
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.get(
            "/api/know/knowledge/relationships/1",
            {"app_id": "myapp"},
        )
        response = RelationshipDetailView.as_view()(
            request, relationship_id=1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["relationship_id"], 1)

    def test_put_missing_app_id_returns_validation_error(self):
        """PUT with missing app_id returns RET_MISSING_PARAM."""
        request = self.factory.put(
            "/api/know/knowledge/relationships/1",
            data={"properties": {"k": "v"}},
            format="json",
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_put_missing_properties_returns_validation_error(self):
        request = self.factory.put(
            "/api/know/knowledge/relationships/1",
            data={"app_id": "myapp"},
            format="json",
        )
        response = RelationshipDetailView.as_view()(
            request, relationship_id=1
        )
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_put_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.update_relationship.return_value = {
            "relationship_id": 1,
            "app_id": "myapp",
            "properties": {"updated": True},
        }
        mock_service_cls.return_value = mock_service
        request = self.factory.put(
            "/api/know/knowledge/relationships/1",
            data={"app_id": "myapp", "properties": {"updated": True}},
            format="json",
        )
        response = RelationshipDetailView.as_view()(
            request, relationship_id=1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["properties"]["updated"], True)

    def test_put_empty_properties_dict_returns_validation_error(self):
        request = self.factory.put(
            "/api/know/knowledge/relationships/1",
            data={"app_id": "myapp", "properties": {}},
            format="json",
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_delete_missing_app_id_returns_validation_error(self):
        """DELETE with missing app_id returns RET_MISSING_PARAM."""
        request = self.factory.delete("/api/know/knowledge/relationships/1")
        response = RelationshipDetailView.as_view()(request, relationship_id=1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_delete_success(self, mock_service_cls):
        """DELETE relationship by id returns OK when service succeeds."""
        mock_service = MagicMock()
        mock_service.delete_relationship.return_value = True
        mock_service_cls.return_value = mock_service
        request = self.factory.delete(
            "/api/know/knowledge/relationships/1?app_id=myapp"
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_delete_not_found(self, mock_service_cls):
        """DELETE relationship not found returns RET_RESOURCE_NOT_FOUND."""
        mock_service = MagicMock()
        mock_service.delete_relationship.side_effect = ValueError("not found")
        mock_service_cls.return_value = mock_service
        request = self.factory.delete(
            "/api/know/knowledge/relationships/999?app_id=myapp"
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=999)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_RESOURCE_NOT_FOUND)

    def test_delete_invalid_relationship_id_returns_invalid_param(self):
        """DELETE with relationship_id=0 returns RET_INVALID_PARAM."""
        request = self.factory.delete(
            "/api/know/knowledge/relationships/0?app_id=myapp"
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)


class RelationshipEndpointIntegrationTest(TestCase):
    """Verify relationship API endpoints are wired and return expected shape. Generated."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_relationship_list_url_resolves(self):
        url = reverse("relationship-list")
        self.assertIn("knowledge/relationships", url)

    def test_relationship_detail_url_resolves(self):
        url = reverse("relationship-detail", kwargs={"relationship_id": 42})
        self.assertIn("knowledge/relationships/42", url)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_get_relationships_via_client_returns_ok_shape(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.query_relationships.return_value = {
            "data": [],
            "total_num": 0,
            "next_offset": None,
        }
        mock_service_cls.return_value = mock_service
        client = APIClient()
        response = client.get(
            reverse("relationship-list"),
            {"app_id": "testapp", "limit": 10, "offset": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIn("data", data["data"])
        self.assertEqual(data["data"]["total_num"], 0)
        self.assertEqual(data["data"]["data"], [])

    def test_query_invalid_limit_or_offset_returns_validation_error(self):
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": "x", "offset": 0},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_post_empty_body_treated_as_empty_dict(self):
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data=None,
            content_type="application/json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_post_service_raises_non_value_error_returns_db_error(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.create_relationship.side_effect = RuntimeError("Neo4j connection failed")
        mock_service_cls.return_value = mock_service
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data={
                "app_id": "myapp",
                "relationship_type": "knowledge_entity",
                "source_knowledge_id": 1,
                "entity_type": "user",
                "entity_id": "e1",
            },
            format="json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["errorCode"], RET_DB_ERROR)

    def test_put_empty_properties_dict_returns_validation_error(self):
        request = self.factory.put(
            "/api/know/knowledge/relationships/1",
            data={"app_id": "myapp", "properties": {}},
            format="json",
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=1)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.relationship_view.RelationshipService")
    def test_post_relationship_via_client_returns_ok_shape(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.create_relationship.return_value = {
            "relationship_id": 1,
            "app_id": "testapp",
            "relationship_type": "knowledge_knowledge",
            "source_knowledge_id": 1,
            "target_knowledge_id": 2,
            "properties": {},
        }
        mock_service_cls.return_value = mock_service
        client = APIClient()
        response = client.post(
            reverse("relationship-list"),
            {"app_id": "testapp", "relationship_type": "knowledge_knowledge", "source_knowledge_id": 1, "target_knowledge_id": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["relationship_type"], "knowledge_knowledge")
        self.assertEqual(data["data"]["target_knowledge_id"], 2)

    def test_put_empty_properties_via_client_returns_validation_error(self):
        client = APIClient()
        response = client.put(
            reverse("relationship-detail", kwargs={"relationship_id": 1}),
            {"app_id": "myapp", "properties": {}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_get_detail_invalid_relationship_id_zero_returns_invalid_param(self):
        """GET relationship detail with relationship_id=0 returns RET_INVALID_PARAM."""
        request = self.factory.get(
            "/api/know/knowledge/relationships/0",
            {"app_id": "myapp"},
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_detail_invalid_relationship_id_non_integer_returns_invalid_param(self):
        """GET relationship detail with relationship_id=abc returns RET_INVALID_PARAM."""
        request = self.factory.get(
            "/api/know/knowledge/relationships/abc",
            {"app_id": "myapp"},
        )
        response = RelationshipDetailView.as_view()(request, relationship_id="abc")
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_put_detail_invalid_relationship_id_returns_invalid_param(self):
        """PUT relationship detail with relationship_id=0 returns RET_INVALID_PARAM."""
        request = self.factory.put(
            "/api/know/knowledge/relationships/0",
            data={"app_id": "myapp", "properties": {"k": "v"}},
            format="json",
        )
        response = RelationshipDetailView.as_view()(request, relationship_id=0)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_list_negative_offset_returns_validation_error(self):
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "offset": "-1", "limit": "10"},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_list_limit_over_max_returns_validation_error(self):
        request = self.factory.get(
            "/api/know/knowledge/relationships",
            {"app_id": "myapp", "limit": str(LIMIT_LIST + 1), "offset": "0"},
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_post_invalid_json_body_returns_parse_error(self):
        """POST with malformed JSON body returns RET_JSON_PARSE_ERROR."""
        request = self.factory.post(
            "/api/know/knowledge/relationships",
            data="{ invalid json }",
            content_type="application/json",
        )
        response = RelationshipListView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_JSON_PARSE_ERROR)
