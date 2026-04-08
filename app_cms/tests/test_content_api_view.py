"""Functional smoke tests for CMS public content API views."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from app_cms.views.content_api_view import CmsContentDetailApiView, CmsContentListApiView
from common.consts.response_const import RET_INVALID_PARAM, RET_OK


class CmsContentApiViewFunctionalTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_unknown_route_returns_404(self, find_meta):
        find_meta.return_value = None
        request = self.factory.get("/api/cms/missing-type/")
        response = CmsContentListApiView.as_view()(request, content_route="missing-type")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("app_cms.views.content_api_view._list_per_page_max", return_value=10)
    @patch("app_cms.views.content_api_view._list_per_page", return_value=5)
    @patch("app_cms.views.content_api_view.ContentReadService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_clamps_per_page_to_max(self, find_meta, read_cls, _lp, _lpmax):
        meta = MagicMock()
        find_meta.return_value = meta
        read_cls.return_value.paginate_published.return_value = Paginator([], 10).get_page(1)

        request = self.factory.get("/api/cms/articles/?per_page=999&page=1")
        response = CmsContentListApiView.as_view()(request, content_route="articles")
        response.render()
        read_cls.return_value.paginate_published.assert_called_once_with(meta, 1, 10)

    @patch("app_cms.views.content_api_view.ContentReadService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_get_success_empty_page(self, find_meta, read_cls):
        find_meta.return_value = MagicMock()
        page_obj = Paginator([], 15).get_page(1)
        read_cls.return_value.paginate_published.return_value = page_obj

        request = self.factory.get("/api/cms/articles/")
        response = CmsContentListApiView.as_view()(request, content_route="articles")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["items"], [])
        self.assertEqual(payload["data"]["pagination"]["total"], 0)
        self.assertEqual(payload["data"]["pagination"]["current_page"], 1)

    @patch("app_cms.views.content_api_view.ContentReadService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_get_maps_rows_via_list_item_array(self, find_meta, read_cls):
        find_meta.return_value = MagicMock()
        page_obj = Paginator([1, 2], 15).get_page(1)
        read_cls.return_value.paginate_published.return_value = page_obj
        read_cls.return_value.list_item_array.side_effect = [
            {"id": 10, "title": "a"},
            {"id": 11, "title": "b"},
        ]

        request = self.factory.get("/api/cms/articles/")
        response = CmsContentListApiView.as_view()(request, content_route="articles")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(len(payload["data"]["items"]), 2)
        self.assertEqual(payload["data"]["items"][0]["id"], 10)

    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_unknown_route_returns_404(self, find_meta):
        find_meta.return_value = None
        request = self.factory.get("/api/cms/missing-type/99/")
        response = CmsContentDetailApiView.as_view()(
            request, content_route="missing-type", record_id="99"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("app_cms.views.content_api_view.ContentReadService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_get_success(self, find_meta, read_cls):
        find_meta.return_value = MagicMock()
        read_cls.return_value.detail_by_pk.return_value = {"id": 5, "title": "row"}

        request = self.factory.get("/api/cms/articles/5/")
        response = CmsContentDetailApiView.as_view()(
            request, content_route="articles", record_id="5"
        )
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 5)

    @patch("app_cms.views.content_api_view.ContentReadService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_get_not_found_raises_404(self, find_meta, read_cls):
        find_meta.return_value = MagicMock()
        read_cls.return_value.detail_by_pk.side_effect = Http404()

        request = self.factory.get("/api/cms/articles/999/")
        response = CmsContentDetailApiView.as_view()(
            request, content_route="articles", record_id="999"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("app_cms.views.content_api_view.ContentPayloadSerializer")
    @patch("app_cms.views.content_api_view.ContentWriteService")
    @patch("app_cms.views.content_api_view.validate_item_payload")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_post_create_success(
        self, find_meta, validate, write_cls, serializer_cls
    ):
        find_meta.return_value = MagicMock()
        validate.return_value = {"title": "new"}
        write_cls.return_value.store.return_value = MagicMock()
        serializer_cls.return_value.detail.return_value = {"id": 7, "title": "new"}

        request = self.factory.post(
            "/api/cms/articles/", data={"title": "new"}, format="json"
        )
        response = CmsContentListApiView.as_view()(request, content_route="articles")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 7)
        validate.assert_called_once()
        call_kw = validate.call_args.kwargs
        self.assertFalse(call_kw["partial"])

    @patch("app_cms.views.content_api_view.validate_item_payload")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_list_post_validation_error_returns_invalid_param(self, find_meta, validate):
        find_meta.return_value = MagicMock()
        validate.side_effect = ValidationError({"title": ["required"]})

        request = self.factory.post("/api/cms/articles/", data={}, format="json")
        response = CmsContentListApiView.as_view()(request, content_route="articles")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_cms.views.content_api_view.ContentPayloadSerializer")
    @patch("app_cms.views.content_api_view.ContentWriteService")
    @patch("app_cms.views.content_api_view.validate_item_payload")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_put_update_success(
        self, find_meta, validate, write_cls, serializer_cls
    ):
        find_meta.return_value = MagicMock()
        validate.return_value = {"title": "upd"}
        write_cls.return_value.update.return_value = MagicMock()
        serializer_cls.return_value.detail.return_value = {"id": 3, "title": "upd"}

        request = self.factory.put(
            "/api/cms/articles/3/", data={"title": "upd"}, format="json"
        )
        response = CmsContentDetailApiView.as_view()(
            request, content_route="articles", record_id="3"
        )
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["title"], "upd")
        self.assertTrue(validate.call_args.kwargs["partial"])

    @patch("app_cms.views.content_api_view.ContentWriteService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_delete_success(self, find_meta, write_cls):
        find_meta.return_value = MagicMock()
        write_cls.return_value.destroy.return_value = None

        request = self.factory.delete("/api/cms/articles/8/")
        response = CmsContentDetailApiView.as_view()(
            request, content_route="articles", record_id="8"
        )
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        write_cls.return_value.destroy.assert_called_once()

    @patch("app_cms.views.content_api_view.ContentWriteService")
    @patch("app_cms.views.content_api_view.CmsContentMeta.find_by_route_segment")
    def test_detail_delete_not_found_returns_404(self, find_meta, write_cls):
        find_meta.return_value = MagicMock()
        write_cls.return_value.destroy.side_effect = Http404()

        request = self.factory.delete("/api/cms/articles/404/")
        response = CmsContentDetailApiView.as_view()(
            request, content_route="articles", record_id="404"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
