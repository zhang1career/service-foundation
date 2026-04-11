"""Tests for keepcon HTTP API views."""

import json
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from common.consts.response_const import RET_INVALID_PARAM

from app_keepcon.views.keepcon_api_view import KeepconHealthView, KeepconInternalDispatchView


def _response_json(response):
    """DRF Response is a TemplateResponse; content requires render() first."""
    if hasattr(response, "render") and callable(response.render):
        response.render()
    return json.loads(response.content.decode())


class TestKeepconHealthView(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_ok(self):
        request = self.factory.get("/api/keepcon/health")
        response = KeepconHealthView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        body = _response_json(response)
        self.assertEqual(body.get("errorCode"), 0)
        self.assertEqual(body.get("data", {}).get("status"), "ok")


class TestKeepconInternalDispatchView(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("app_keepcon.views.keepcon_api_view.dispatch_to_device")
    @patch("app_keepcon.views.keepcon_api_view.get_reg_by_access_key_and_status")
    def test_post_success(self, mock_reg, mock_dispatch):
        mock_reg.return_value = MagicMock()
        mock_dispatch.return_value = {"msg_id": 1, "seq": 1, "device_key": "d", "status": 0}
        request = self.factory.post(
            "/api/keepcon/internal/messages",
            data=json.dumps(
                {
                    "access_key": "ak",
                    "device_key": "d",
                    "payload": {"a": 1},
                }
            ),
            content_type="application/json",
        )
        response = KeepconInternalDispatchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        self.assertEqual(args[0], "d")
        self.assertEqual(args[1], {"a": 1})
        self.assertIsNone(args[2])

    @patch("app_keepcon.views.keepcon_api_view.get_reg_by_access_key_and_status")
    def test_post_invalid_access_key(self, mock_reg):
        mock_reg.return_value = None
        request = self.factory.post(
            "/api/keepcon/internal/messages",
            data=json.dumps(
                {
                    "access_key": "bad",
                    "device_key": "d",
                    "payload": {},
                }
            ),
            content_type="application/json",
        )
        response = KeepconInternalDispatchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        body = _response_json(response)
        self.assertEqual(body.get("errorCode"), RET_INVALID_PARAM)

    @patch("app_keepcon.views.keepcon_api_view.dispatch_to_device")
    @patch("app_keepcon.views.keepcon_api_view.get_reg_by_access_key_and_status")
    def test_post_idempotency_alias(self, mock_reg, mock_dispatch):
        mock_reg.return_value = MagicMock()
        mock_dispatch.return_value = {"msg_id": 2, "seq": 1, "device_key": "d", "status": 0}
        request = self.factory.post(
            "/api/keepcon/internal/messages",
            data=json.dumps(
                {
                    "access_key": "ak",
                    "device_key": "d",
                    "payload": {},
                    "idempotency_key": "idem-1",
                }
            ),
            content_type="application/json",
        )
        KeepconInternalDispatchView.as_view()(request)
        self.assertEqual(mock_dispatch.call_args[0][2], "idem-1")
