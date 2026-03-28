from unittest import TestCase
from unittest.mock import MagicMock, patch

from common.services.http import client as http_client_module


class HttpClientTest(TestCase):
    def tearDown(self):
        http_client_module._CLIENTS.clear()

    @patch("common.services.http.client.httpx.Client")
    def test_get_http_client_default_pool_and_reuse(self, client_cls):
        client_instance = MagicMock()
        client_cls.return_value = client_instance

        c1 = http_client_module.get_http_client(pool_name="")
        c2 = http_client_module.get_http_client(pool_name=None)

        self.assertIs(c1, c2)
        client_cls.assert_called_once()
        self.assertIn("thirdparty_pool", http_client_module._CLIENTS)

    @patch("common.services.http.client.httpx.Client")
    def test_get_http_client_timeout_override_for_reused_client(self, client_cls):
        client_instance = MagicMock()
        client_cls.return_value = client_instance
        http_client_module.get_http_client(pool_name="webhook_pool")

        http_client_module.get_http_client(pool_name="webhook_pool", timeout_sec=3)
        self.assertIsNotNone(client_instance.timeout)

    def test_close_all_clients_closes_and_clears(self):
        c1 = MagicMock()
        c2 = MagicMock()
        http_client_module._CLIENTS["a"] = c1
        http_client_module._CLIENTS["b"] = c2

        http_client_module.close_all_http_clients()

        c1.close.assert_called_once()
        c2.close.assert_called_once()
        self.assertEqual(http_client_module._CLIENTS, {})
