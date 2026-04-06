from unittest import TestCase

from common.utils.redis_url_util import redis_location_with_db


class TestRedisLocationWithDb(TestCase):
    def test_appends_db_to_base_without_path(self):
        self.assertEqual(
            redis_location_with_db("redis://127.0.0.1:6379", 1),
            "redis://127.0.0.1:6379/1",
        )

    def test_replaces_trailing_db_segment(self):
        self.assertEqual(
            redis_location_with_db("redis://127.0.0.1:6379/1", 2),
            "redis://127.0.0.1:6379/2",
        )
