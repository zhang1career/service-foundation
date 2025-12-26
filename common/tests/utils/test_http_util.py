from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_with_type(self):
        # lazy load
        from common.utils.http_util import with_type

        # normal case
        origin_data = {
            "id": "1",
            "name": "a",
            "age": 18,
            "is_active": "true",
            "children": [
                {
                    "id": "2",
                    "name": "b",
                    "is_active": "false"
                }
            ],
            "is_deleted": None,
            "is_deleted2": "null",
        }
        expected_result = {
            "id": 1,
            "name": "a",
            "age": 18,
            "is_active": True,
            "children": [
                {
                    "id": 2,
                    "name": "b",
                    "is_active": False
                }
            ],
            "is_deleted": None,
            "is_deleted2": "null"
        }
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)

        # empty case
        origin_data = {}
        expected_result = {}
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)

        # None case
        origin_data = None
        expected_result = None
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)