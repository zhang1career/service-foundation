from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from common.services.http import HttpCallError

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter


class DummyAdapter(BaseHttpAdapter):
    adapter_name = "dummy"


class TestBaseHttpAdapter(SimpleTestCase):
    def test_init_requires_base_url(self):
        with self.assertRaisesMessage(ValueError, "dummy base url is required"):
            DummyAdapter(base_url="")

    def test_headers_bearer(self):
        a = DummyAdapter(base_url="http://example.com", api_key="k", auth_mode="bearer")
        h = a._headers()
        self.assertEqual(h["Authorization"], "Bearer k")
        self.assertNotIn("api-key", h)

    def test_headers_api_key_mode(self):
        a = DummyAdapter(base_url="http://example.com", api_key="secret", auth_mode="api-key")
        h = a._headers()
        self.assertEqual(h["api-key"], "secret")

    def test_headers_opensearch_mode(self):
        a = DummyAdapter(base_url="http://example.com", api_key="osk", auth_mode="opensearch")
        h = a._headers()
        self.assertEqual(h["Authorization"], "ApiKey osk")

    @patch("app_searchrec.adapters.base_http_adapter.request_sync")
    def test_request_raw_success(self, mock_sync):
        mock_resp = MagicMock()
        mock_sync.return_value = mock_resp
        a = DummyAdapter(base_url="http://example.com")
        r = a._request_raw(method="GET", path="/p")
        self.assertIs(r, mock_resp)
        mock_sync.assert_called_once()
        call_kw = mock_sync.call_args[1]
        self.assertEqual(call_kw["url"], "http://example.com/p")

    @patch("app_searchrec.adapters.base_http_adapter.request_sync")
    def test_request_raw_wraps_http_call_error(self, mock_sync):
        mock_sync.side_effect = HttpCallError("timeout")
        a = DummyAdapter(base_url="http://example.com")
        with self.assertRaises(RuntimeError) as ctx:
            a._request_raw(method="GET", path="/p")
        self.assertIn("dummy request failed", str(ctx.exception))

    def test_request_raises_on_error_status(self):
        a = DummyAdapter(base_url="http://example.com")
        bad = MagicMock()
        bad.status_code = 500
        bad.text = "err"
        with patch.object(a, "_request_raw", return_value=bad):
            with self.assertRaises(RuntimeError) as ctx:
                a._request(method="GET", path="/p")
        self.assertIn("status=500", str(ctx.exception))

    def test_request_returns_on_2xx(self):
        a = DummyAdapter(base_url="http://example.com")
        ok = MagicMock()
        ok.status_code = 200
        with patch.object(a, "_request_raw", return_value=ok):
            self.assertIs(a._request(method="GET", path="/p"), ok)
