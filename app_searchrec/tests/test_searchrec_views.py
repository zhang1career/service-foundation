import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_searchrec.views.searchrec_view import (
    SearchRecHealthView,
    SearchRecIndexUpsertView,
    SearchRecRankView,
    SearchRecRecommendView,
    SearchRecSearchView,
)
from common.consts.response_const import RET_INVALID_PARAM, RET_OK
from common.utils.django_util import setting_str


def _request_id_response_header() -> str:
    return setting_str("REQUEST_ID_RESPONSE_HEADER", "X-Request-Id")


def _active_reg_mock():
    r = MagicMock()
    r.id = 1
    return r


class SearchRecViewsFunctionalTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_health(self):
        request = self.factory.get("/api/searchrec/health")
        response = SearchRecHealthView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["status"], "ok")

    def test_health_response_includes_request_id_header(self):
        header_name = _request_id_response_header()
        request = self.factory.get("/api/searchrec/health")
        response = SearchRecHealthView.as_view()(request)
        response.render()
        self.assertIn(header_name, response)
        self.assertEqual(len(response[header_name]), 16)

    def test_health_echoes_client_x_request_id(self):
        header_name = _request_id_response_header()
        request = self.factory.get("/api/searchrec/health", HTTP_X_REQUEST_ID="client-rid-9")
        response = SearchRecHealthView.as_view()(request)
        response.render()
        self.assertEqual(response[header_name], "client-rid-9")

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_index_upsert_success(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.upsert_documents.return_value = {"upserted": 2}
        request = self.factory.post(
            "/api/searchrec/index",
            data={"access_key": "k", "documents": [{"id": "1"}, {"id": "2"}]},
            format="json",
        )
        response = SearchRecIndexUpsertView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["upserted"], 2)

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_invalid_payload(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.search.side_effect = ValueError("query is required")
        request = self.factory.post(
            "/api/searchrec/search",
            data={"access_key": "k", "query": ""},
            format="json",
        )
        response = SearchRecSearchView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_recommend_success(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.recommend.return_value = {"total_hits": 1, "items": [{"id": "doc1"}]}
        request = self.factory.post(
            "/api/searchrec/recommend",
            data={"access_key": "k", "user_profile": {"preferred_tags": ["x"]}},
            format="json",
        )
        response = SearchRecRecommendView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["items"][0]["id"], "doc1")

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_success(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.rank.return_value = {"items": [{"id": "A"}]}
        request = self.factory.post(
            "/api/searchrec/rank",
            data={
                "access_key": "k",
                "candidates": [{"id": "A", "base_score": 1}],
                "strategy": "hybrid",
            },
            format="json",
        )
        response = SearchRecRankView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_null_preferred_tags_becomes_empty_list(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.search.return_value = {"items": [], "total_hits": 0}
        request = self.factory.post(
            "/api/searchrec/search",
            data={"access_key": "k", "query": "q", "preferred_tags": None},
            format="json",
        )
        SearchRecSearchView.as_view()(request)
        service_cls.search.assert_called_once_with(1, query="q", top_k=10, preferred_tags=[])

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_null_strategy_uses_hybrid(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.rank.return_value = {"items": []}
        request = self.factory.post(
            "/api/searchrec/rank",
            data={"access_key": "k", "candidates": [], "strategy": None},
            format="json",
        )
        SearchRecRankView.as_view()(request)
        service_cls.rank.assert_called_once_with(candidates=[], strategy="hybrid")

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    def test_index_upsert_empty_documents_returns_invalid_param(self, get_reg):
        get_reg.return_value = _active_reg_mock()
        header_name = _request_id_response_header()
        request = self.factory.post(
            "/api/searchrec/index",
            data={"access_key": "k", "documents": []},
            format="json",
            HTTP_X_REQUEST_ID="err-rid-1",
        )
        response = SearchRecIndexUpsertView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertEqual(response[header_name], "err-rid-1")

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_search_value_error_returns_invalid_param(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.search.side_effect = ValueError("bad query")
        request = self.factory.post(
            "/api/searchrec/search",
            data={"access_key": "k", "query": "x"},
            format="json",
        )
        response = SearchRecSearchView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("bad query", payload["message"])

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_recommend_value_error_returns_invalid_param(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.recommend.side_effect = ValueError("bad profile")
        request = self.factory.post(
            "/api/searchrec/recommend",
            data={"access_key": "k"},
            format="json",
        )
        response = SearchRecRecommendView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    @patch("app_searchrec.views.searchrec_view.SearchRecService")
    def test_rank_value_error_returns_invalid_param(self, service_cls, get_reg):
        get_reg.return_value = _active_reg_mock()
        service_cls.rank.side_effect = ValueError("bad candidates")
        request = self.factory.post(
            "/api/searchrec/rank",
            data={"access_key": "k", "candidates": []},
            format="json",
        )
        response = SearchRecRankView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
