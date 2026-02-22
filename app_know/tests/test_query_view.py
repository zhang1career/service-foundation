"""
Tests for logical query API view (GET/POST). Generated.
Round 2: skills-scoped query tests (app_id=skills).
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient

from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import RET_OK, RET_MISSING_PARAM, RET_INVALID_PARAM, RET_DB_ERROR, RET_JSON_PARSE_ERROR

from app_know.repos.summary_repo import QUERY_SEARCH_MAX_LEN
from app_know.views.query_view import LogicalQueryView


class LogicalQueryViewTest(TestCase):
    """Tests for GET/POST knowledge/query."""

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [{"type": "knowledge", "knowledge_id": 1}], "total_num": 1}
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get("/api/know/knowledge/query", {"query": "test", "app_id": "myapp"})
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(len(data["data"]["data"]), 1)
        mock_svc.query.assert_called_once()
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "test")
        self.assertEqual(call_kw["app_id"], "myapp")

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_with_q_param(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc

        request = self.factory.get("/api/know/knowledge/query", {"q": "keyword"})
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "keyword")

    def test_get_missing_query(self):
        request = self.factory.get("/api/know/knowledge/query")
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertNotEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_get_invalid_limit(self):
        request = self.factory.get("/api/know/knowledge/query", {"query": "x", "limit": "big"})
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_limit_boundary_one(self):
        """GET with limit=1 is valid."""
        with patch("app_know.views.query_view.LogicalQueryService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.query.return_value = {"data": [], "total_num": 0}
            mock_svc_cls.return_value = mock_svc
            request = self.factory.get("/api/know/knowledge/query", {"query": "x", "limit": "1"})
            response = LogicalQueryView.as_view()(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_svc.query.assert_called_once()
            self.assertEqual(mock_svc.query.call_args[1]["limit"], 1)

    def test_get_limit_boundary_max(self):
        """GET with limit=LIMIT_LIST is valid."""
        with patch("app_know.views.query_view.LogicalQueryService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.query.return_value = {"data": [], "total_num": 0}
            mock_svc_cls.return_value = mock_svc
            request = self.factory.get(
                "/api/know/knowledge/query", {"query": "x", "limit": str(LIMIT_LIST)}
            )
            response = LogicalQueryView.as_view()(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(mock_svc.query.call_args[1]["limit"], LIMIT_LIST)

    def test_get_limit_zero_returns_invalid_param(self):
        request = self.factory.get("/api/know/knowledge/query", {"query": "x", "limit": "0"})
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_limit_over_max_returns_invalid_param(self):
        request = self.factory.get(
            "/api/know/knowledge/query", {"query": "x", "limit": str(LIMIT_LIST + 1)}
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_get_query_too_long_returns_invalid_param(self):
        request = self.factory.get(
            "/api/know/knowledge/query",
            {"query": "x" * (QUERY_SEARCH_MAX_LEN + 1)},
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)
        self.assertIn("exceed", data.get("message", "").lower())

    def test_post_empty_body_treated_as_missing_query(self):
        """POST with empty JSON body yields missing query."""
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_post_invalid_json_returns_parse_error(self):
        request = self.factory.post(
            "/api/know/knowledge/query",
            data="{ invalid }",
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_JSON_PARSE_ERROR)

    def test_post_query_too_long_returns_invalid_param(self):
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "x" * (QUERY_SEARCH_MAX_LEN + 1)}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_service_raises_returns_db_error(self, mock_svc_cls):
        mock_svc_cls.return_value.query.side_effect = RuntimeError("Atlas connection failed")
        request = self.factory.get("/api/know/knowledge/query", {"query": "test"})
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_DB_ERROR)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_service_raises_returns_db_error(self, mock_svc_cls):
        mock_svc_cls.return_value.query.side_effect = OSError("Neo4j error")
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "test"}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_DB_ERROR)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc

        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "natural language", "app_id": "app1", "limit": 20}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "natural language")
        self.assertEqual(call_kw["limit"], 20)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_skills_scoped_query_calls_service_with_app_id_skills(self, mock_svc_cls):
        """Skills-scoped query: GET with app_id=skills invokes service with app_id='skills' (Atlas + Neo4j)."""
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc
        request = self.factory.get(
            "/api/know/knowledge/query",
            {"query": "python programming", "app_id": "skills", "limit": "10"},
        )
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_svc.query.assert_called_once()
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "python programming")
        self.assertEqual(call_kw["app_id"], "skills")
        self.assertEqual(call_kw["limit"], 10)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_skills_scoped_query_calls_service_with_app_id_skills(self, mock_svc_cls):
        """Skills-scoped query: POST with app_id=skills invokes service with app_id='skills'."""
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "machine learning", "app_id": "skills", "limit": 20}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_svc.query.assert_called_once()
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["app_id"], "skills")

    def test_post_missing_query(self):
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"app_id": "app1"}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_json_body_from_raw_body_parsed(self, mock_svc_cls):
        """POST with JSON in request.body (no request.data) is parsed correctly (edge case)."""
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "from body", "limit": 5}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "from body")
        self.assertEqual(call_kw["limit"], 5)


class LogicalQueryEndpointTest(TestCase):
    """Verify knowledge/query endpoint is wired and returns expected shape. Generated."""

    def test_knowledge_query_url_resolves(self):
        url = reverse("knowledge-query")
        self.assertIn("knowledge/query", url)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_query_via_client_returns_ok_shape(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [{"type": "knowledge", "knowledge_id": 1}], "total_num": 1}
        mock_svc_cls.return_value = mock_svc
        client = APIClient()
        response = client.get(reverse("knowledge-query"), {"query": "test", "app_id": "myapp"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertIn("data", data["data"])
        self.assertIn("total_num", data["data"])
        self.assertEqual(data["data"]["total_num"], 1)
        self.assertEqual(len(data["data"]["data"]), 1)
        self.assertEqual(data["data"]["data"][0]["knowledge_id"], 1)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_query_via_client_returns_ok_shape(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [], "total_num": 0}
        mock_svc_cls.return_value = mock_svc
        client = APIClient()
        response = client.post(
            reverse("knowledge-query"),
            {"query": "natural language", "app_id": "app1", "limit": 20},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 0)
        mock_svc.query.assert_called_once()
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["query"], "natural language")
        self.assertEqual(call_kw["limit"], 20)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_skills_scoped_query_via_client_returns_ok(self, mock_svc_cls):
        """Verify knowledge/query endpoint with app_id=skills (skills-scoped) returns OK and service called correctly."""
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [{"type": "knowledge", "knowledge_id": 1}], "total_num": 1}
        mock_svc_cls.return_value = mock_svc
        client = APIClient()
        response = client.get(reverse("knowledge-query"), {"query": "skill", "app_id": "skills"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 1)
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["app_id"], "skills")
