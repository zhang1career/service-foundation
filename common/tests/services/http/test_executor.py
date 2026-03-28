from unittest import TestCase
from unittest.mock import MagicMock, patch

import httpx

from common.services.http.executor import HttpCallError, _normalize_data, _queue_for_pool, request_sync


class HttpExecutorTest(TestCase):
    def test_normalize_data_bytes_and_str(self):
        self.assertEqual(_normalize_data(b"\x01"), {"_type": "bytes", "value": "\x01"})
        self.assertEqual(_normalize_data("abc"), {"_type": "str", "value": "abc"})
        self.assertIsNone(_normalize_data(None))

    def test_normalize_data_non_serializable_raises(self):
        with self.assertRaises(TypeError):
            _normalize_data({"x": {1, 2}})

    def test_queue_for_pool(self):
        self.assertEqual(_queue_for_pool("avatar_http_pool"), "avatar")
        self.assertEqual(_queue_for_pool("webhook_pool"), "webhook")
        self.assertEqual(_queue_for_pool("thirdparty_pool"), "thirdparty")

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_success(self, get_client_mock):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        client.request.return_value = response
        get_client_mock.return_value = client

        ret = request_sync(method="get", url="https://example.com")
        self.assertIs(ret, response)
        client.request.assert_called_once()

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_wraps_httpx_error(self, get_client_mock):
        client = MagicMock()
        client.request.side_effect = httpx.ConnectError("boom")
        get_client_mock.return_value = client

        with self.assertRaises(HttpCallError):
            request_sync(method="get", url="https://example.com")
