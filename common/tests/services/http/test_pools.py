from unittest import TestCase

from common.services.http.pools import HttpClientPool, pool_id


class HttpPoolsTest(TestCase):
    def test_pool_id_defaults_for_none_and_empty(self):
        default = HttpClientPool.THIRD_PARTY.value
        self.assertEqual(pool_id(None), default)
        self.assertEqual(pool_id(""), default)

    def test_pool_id_from_enum_and_str(self):
        self.assertEqual(pool_id(HttpClientPool.WEBHOOK), HttpClientPool.WEBHOOK.value)
        self.assertEqual(pool_id("custom_pl"), "custom_pl")

    def test_http_client_pool_enum_values_distinct(self):
        self.assertNotEqual(
            HttpClientPool.THIRD_PARTY.value,
            HttpClientPool.WEBHOOK.value,
        )
