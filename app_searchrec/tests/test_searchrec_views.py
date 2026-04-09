import json
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from app_searchrec.views.searchrec_view import (
    SearchRecHealthView,
    SearchRecIndexUpsertView,
    SearchRecRankView,
    SearchRecRecommendView,
    SearchRecSearchView,
)
from common.consts.response_const import RET_INVALID_PARAM, RET_OK


class SearchRecViewsFunctionalTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_health(self):
        request = self.factory.get("/api/searchrec/health")
        response = SearchRecHealthView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["status"], "ok")

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_index_upsert_success(self, service_cls):
        service_cls.upsert_documents.return_value = {"upserted": 2}
        request = self.factory.post(
            "/api/searchrec/index/upsert",
            data={"documents": [{"id": "1"}, {"id": "2"}]},
            format="json",
        )
        response = SearchRecIndexUpsertView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["upserted"], 2)

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_invalid_payload(self, service_cls):
        service_cls.search.side_effect = ValueError("query is required")
        request = self.factory.post("/api/searchrec/search", data={"query": ""}, format="json")
        response = SearchRecSearchView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_recommend_success(self, service_cls):
        service_cls.recommend.return_value = {"total_hits": 1, "items": [{"id": "doc1"}]}
        request = self.factory.post(
            "/api/searchrec/recommend",
            data={"user_profile": {"preferred_tags": ["x"]}},
            format="json",
        )
        response = SearchRecRecommendView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["items"][0]["id"], "doc1")

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_success(self, service_cls):
        service_cls.rank.return_value = {"items": [{"id": "A"}]}
        request = self.factory.post(
            "/api/searchrec/rank",
            data={"candidates": [{"id": "A", "base_score": 1}], "strategy": "hybrid"},
            format="json",
        )
        response = SearchRecRankView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_null_preferred_tags_becomes_empty_list(self, service_cls):
        service_cls.search.return_value = {"items": [], "total_hits": 0}
        request = self.factory.post(
            "/api/searchrec/search",
            data={"query": "q", "preferred_tags": None},
            format="json",
        )
        SearchRecSearchView.as_view()(request)
        service_cls.search.assert_called_once_with(query="q", top_k=10, preferred_tags=[])

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_null_strategy_uses_hybrid(self, service_cls):
        service_cls.rank.return_value = {"items": []}
        request = self.factory.post(
            "/api/searchrec/rank",
            data={"candidates": [], "strategy": None},
            format="json",
        )
        SearchRecRankView.as_view()(request)
        service_cls.rank.assert_called_once_with(candidates=[], strategy="hybrid")

    def test_index_upsert_empty_documents_returns_invalid_param(self):
        request = self.factory.post("/api/searchrec/index/upsert", data={"documents": []}, format="json")
        response = SearchRecIndexUpsertView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_value_error_returns_invalid_param(self, service_cls):
        service_cls.search.side_effect = ValueError("bad query")
        request = self.factory.post("/api/searchrec/search", data={"query": "x"}, format="json")
        response = SearchRecSearchView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("bad query", payload["message"])

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_recommend_value_error_returns_invalid_param(self, service_cls):
        service_cls.recommend.side_effect = ValueError("bad profile")
        request = self.factory.post("/api/searchrec/recommend", data={}, format="json")
        response = SearchRecRecommendView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_value_error_returns_invalid_param(self, service_cls):
        service_cls.rank.side_effect = ValueError("bad candidates")
        request = self.factory.post("/api/searchrec/rank", data={"candidates": []}, format="json")
        response = SearchRecRankView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
