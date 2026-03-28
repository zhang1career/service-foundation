from unittest import TestCase
from unittest.mock import MagicMock, patch

from common.consts.response_const import RET_OK

from app_aibroker.http_transport import aibroker_http_post, aibroker_http_post_embeddings


class HttpTransportTest(TestCase):
    @patch("app_aibroker.http_transport.settings")
    @patch("app_aibroker.http_transport.request_sync")
    def test_post_success_returns_data_object(self, request_sync_mock, settings_mock):
        settings_mock.AIBROKER_SERVICE_URL = "https://aib.example.com"
        settings_mock.KNOW_AIBROKER_ACCESS_KEY = "ak"
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"errorCode": RET_OK, "data": {"text": "hello"}}
        request_sync_mock.return_value = resp

        data = aibroker_http_post({"prompt": "hi", "temperature": 0.7})
        self.assertEqual(data, {"text": "hello"})
        call_kw = request_sync_mock.call_args.kwargs
        self.assertEqual(call_kw["json_body"]["access_key"], "ak")
        self.assertEqual(call_kw["url"], "https://aib.example.com/v1/text/generate")

    @patch("app_aibroker.http_transport.settings")
    @patch("app_aibroker.http_transport.request_sync")
    def test_post_error_code_raises(self, request_sync_mock, settings_mock):
        settings_mock.AIBROKER_SERVICE_URL = "https://aib.example.com"
        settings_mock.KNOW_AIBROKER_ACCESS_KEY = "ak"
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"errorCode": 1, "message": "bad"}
        request_sync_mock.return_value = resp

        with self.assertRaises(RuntimeError):
            aibroker_http_post({})

    @patch("app_aibroker.http_transport.settings")
    def test_missing_root_or_key_raises(self, settings_mock):
        settings_mock.AIBROKER_SERVICE_URL = ""
        settings_mock.KNOW_AIBROKER_ACCESS_KEY = ""
        with self.assertRaises(RuntimeError):
            aibroker_http_post_embeddings({})
