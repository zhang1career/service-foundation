import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from app_know.services.query_service import QUERY_SEARCH_MAX_LEN
from app_know.views.query_view import LogicalQueryView
from common.consts.response_const import (
    RET_DB_ERROR,
    RET_INVALID_PARAM,
    RET_JSON_PARSE_ERROR,
    RET_MISSING_PARAM,
    RET_OK,
)


class LogicalQueryViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_get_success(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"data": [{"type": "knowledge", "knowledge_id": 1}], "total_num": 1}
        mock_svc_cls.return_value = mock_svc
        request = self.factory.get("/api/know/knowledge/query", {"query": "test"})
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_OK)
        self.assertEqual(data["data"]["total_num"], 1)

    def test_get_missing_query(self):
        request = self.factory.get("/api/know/knowledge/query")
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_MISSING_PARAM)

    def test_get_query_too_long(self):
        request = self.factory.get(
            "/api/know/knowledge/query",
            {"query": "x" * (QUERY_SEARCH_MAX_LEN + 1)},
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_INVALID_PARAM)

    def test_post_invalid_json(self):
        request = self.factory.post(
            "/api/know/knowledge/query",
            data="{ invalid }",
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_JSON_PARSE_ERROR)

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_post_triple_format(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.query.return_value = {"triples": [], "candidates": [], "total_candidates": 0, "total_triples": 0}
        mock_svc_cls.return_value = mock_svc
        request = self.factory.post(
            "/api/know/knowledge/query",
            data=json.dumps({"query": "test", "format": "triple"}),
            content_type="application/json",
        )
        response = LogicalQueryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_kw = mock_svc.query.call_args[1]
        self.assertEqual(call_kw["output_format"], "triple")

    @patch("app_know.views.query_view.LogicalQueryService")
    def test_service_error_returns_db_error(self, mock_svc_cls):
        mock_svc_cls.return_value.query.side_effect = RuntimeError("Graphiti down")
        request = self.factory.get("/api/know/knowledge/query", {"query": "test"})
        response = LogicalQueryView.as_view()(request)
        response.render()
        data = json.loads(response.content)
        self.assertEqual(data["errorCode"], RET_DB_ERROR)
