"""Tests for config HTTP query views (pub/pri: X-Config-Access-Key; pub also X-Config-Key)."""

import json
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_config.views.config_query_view import ConfigPriQueryView, ConfigPubQueryView
from common.consts.response_const import RET_INVALID_PARAM


class _FakeReg:
    def __init__(self, pk: int):
        self.id = pk


class ConfigPubQueryViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_config.views.config_query_view.query_cache_set")
    @patch("app_config.views.config_query_view.merge_config_query_result")
    @patch("app_config.views.config_query_view.query_cache_get", return_value=None)
    @patch("app_config.views.config_query_view.get_reg_by_access_key_and_status")
    def test_get_pub_ok_reads_headers(
        self, mock_get_reg, _cache_get, mock_merge, _cache_set
    ):
        mock_get_reg.return_value = _FakeReg(7)
        mock_merge.return_value = {"value": {"x": 1}, "_ids": "10"}
        request = self.factory.get(
            "/api/config/pub",
            **{
                "HTTP_X_CONFIG_ACCESS_KEY": "ak",
                "HTTP_X_CONFIG_KEY": "app.feature",
            },
        )
        response = ConfigPubQueryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["errorCode"], 0)
        self.assertEqual(payload["data"]["value"], {"x": 1})
        mock_get_reg.assert_called_once()
        mock_merge.assert_called_once()

    @patch("app_config.views.config_query_view.get_reg_by_access_key_and_status")
    def test_get_pub_query_access_key_ignored(self, mock_get_reg):
        mock_get_reg.return_value = _FakeReg(1)
        with patch(
            "app_config.views.config_query_view.query_cache_get", return_value=None
        ), patch(
            "app_config.views.config_query_view.merge_config_query_result",
            return_value={"value": None, "_ids": ""},
        ), patch("app_config.views.config_query_view.query_cache_set"):
            request = self.factory.get(
                "/api/config/pub?access_key=from_query&key=from_q",
                **{
                    "HTTP_X_CONFIG_ACCESS_KEY": "from_header",
                    "HTTP_X_CONFIG_KEY": "app.k",
                },
            )
            ConfigPubQueryView.as_view()(request)
        mock_get_reg.assert_called_once()
        args, _kw = mock_get_reg.call_args
        self.assertEqual(args[0], "from_header")

    def test_get_pub_missing_access_key_header(self):
        request = self.factory.get(
            "/api/config/pub",
            **{"HTTP_X_CONFIG_KEY": "app.k"},
        )
        response = ConfigPubQueryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("access_key", payload["message"])

    def test_get_pub_missing_config_key_header(self):
        request = self.factory.get(
            "/api/config/pub",
            **{"HTTP_X_CONFIG_ACCESS_KEY": "ak"},
        )
        response = ConfigPubQueryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("key", payload["message"])

    @patch("app_config.views.config_query_view.get_reg_by_access_key_and_status")
    def test_get_pub_conditions_from_query(self, mock_get_reg):
        mock_get_reg.return_value = _FakeReg(1)
        with patch(
            "app_config.views.config_query_view.query_cache_get", return_value=None
        ) as mock_cache_get, patch(
            "app_config.views.config_query_view.merge_config_query_result",
            return_value={"value": {}, "_ids": ""},
        ) as mock_merge, patch("app_config.views.config_query_view.query_cache_set"):
            request = self.factory.get(
                "/api/config/pub?conditions=%7B%22env%22%3A%22p%22%7D",
                **{
                    "HTTP_X_CONFIG_ACCESS_KEY": "ak",
                    "HTTP_X_CONFIG_KEY": "app.k",
                },
            )
            ConfigPubQueryView.as_view()(request)
        mock_merge.assert_called_once()
        pos_args, _kw = mock_merge.call_args
        self.assertEqual(pos_args[2], {"env": "p"})
        mock_cache_get.assert_called_once()


class ConfigPriQueryViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _without_auth(self):
        return patch.multiple(
            ConfigPriQueryView,
            permission_classes=[],
            authentication_classes=[],
        )

    @patch("app_config.views.config_query_view.query_cache_set")
    @patch("app_config.views.config_query_view.merge_config_query_result")
    @patch("app_config.views.config_query_view.query_cache_get", return_value=None)
    @patch("app_config.views.config_query_view.get_reg_by_access_key_and_status")
    def test_post_pri_ok_reads_access_key_header(
        self, mock_get_reg, _cache_get, mock_merge, _cache_set
    ):
        mock_get_reg.return_value = _FakeReg(3)
        mock_merge.return_value = {
            "value": {},
            "_ids": "",
            "_explain": {"conditions_received": {}, "matched_layers": []},
        }
        with self._without_auth():
            request = self.factory.post(
                "/api/config/pri",
                data={"key": "app.k"},
                format="json",
                HTTP_X_CONFIG_ACCESS_KEY="ak_pri",
            )
            response = ConfigPriQueryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["errorCode"], 0)
        self.assertEqual(mock_get_reg.call_args[0][0], "ak_pri")

    @patch("app_config.views.config_query_view.get_reg_by_access_key_and_status")
    def test_post_pri_body_access_key_ignored(self, mock_get_reg):
        mock_get_reg.return_value = _FakeReg(1)
        with self._without_auth(), patch(
            "app_config.views.config_query_view.query_cache_get", return_value=None
        ), patch(
            "app_config.views.config_query_view.merge_config_query_result",
            return_value={
                "value": None,
                "_ids": "",
                "_explain": {"conditions_received": {}, "matched_layers": []},
            },
        ), patch("app_config.views.config_query_view.query_cache_set"):
            request = self.factory.post(
                "/api/config/pri",
                data={"access_key": "from_body", "key": "app.k"},
                format="json",
                HTTP_X_CONFIG_ACCESS_KEY="from_header",
            )
            ConfigPriQueryView.as_view()(request)
        args, _kw = mock_get_reg.call_args
        self.assertEqual(args[0], "from_header")

    def test_post_pri_missing_access_key_header(self):
        with self._without_auth():
            request = self.factory.post(
                "/api/config/pri",
                data={"key": "app.k"},
                format="json",
            )
            response = ConfigPriQueryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("access_key", payload["message"])
