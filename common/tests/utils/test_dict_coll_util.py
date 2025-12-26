from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_add_to_list(self):
        # lazy load
        from common.utils.dict_coll_util import add_to_list

        # normal case
        given_dict = {}
        key = "key"
        value = "value"
        expected_result = {"key": ["value"]}
        add_to_list(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # there is a value before append case
        given_dict = {"key": ["value"]}
        key = "key"
        value = "value2"
        expected_result = {"key": ["value", "value2"]}
        add_to_list(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "key"
        value = "value"
        expected_result = {"key": ["value"]}
        add_to_list(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

    def test_add_to_set(self):
        # lazy load
        from common.utils.dict_coll_util import add_to_set

        # normal case
        given_dict = {}
        key = "key"
        value = "value"
        expected_result = {"key": {"value"}}
        add_to_set(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # there is a value before update case
        given_dict = {"key": {"value"}}
        key = "key"
        value = "value2"
        expected_result = {"key": {"value", "value2"}}
        add_to_set(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "key"
        value = "value"
        expected_result = {"key": {"value"}}
        add_to_set(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

    def test_update_to_set(self):
        # lazy load
        from common.utils.dict_coll_util import update_to_set

        # normal case
        given_dict = {}
        key = "key"
        value_set = {"value"}
        expected_result = {"key": {"value"}}
        update_to_set(given_dict, key, value_set)
        self.assertEqual(expected_result, given_dict)

        # there is a value before update case
        given_dict = {"key": {"value"}}
        key = "key"
        value_set = {"value2"}
        expected_result = {"key": {"value", "value2"}}
        update_to_set(given_dict, key, value_set)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "key"
        value_set = {"value"}
        expected_result = {"key": {"value"}}
        update_to_set(given_dict, key, value_set)
        self.assertEqual(expected_result, given_dict)

    def test_add_to_dict(self):
        # lazy load
        from common.utils.dict_coll_util import add_to_dict

        # normal case
        given_dict = {}
        key = "a"
        value = {"b": "c"}
        expected_result = {"a": {"b": "c"}}
        add_to_dict(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # there is a value before update case
        given_dict = {"a": {"b": "c"}}
        key = "a"
        value = {"b2": "c2"}
        expected_result = {"a": {"b": "c", "b2": "c2"}}
        add_to_dict(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "a"
        value = {"b": "c"}
        expected_result = {"a": {"b": "c"}}
        add_to_dict(given_dict, key, value)
        self.assertEqual(expected_result, given_dict)

    def test_add_to_dict_set(self):
        # lazy load
        from common.utils.dict_coll_util import add_to_dict_set

        # normal case
        given_dict = {}
        key = "a"
        sub_key = "b"
        value = "c"
        expected_result = {"a": {"b": {"c"}}}
        add_to_dict_set(given_dict, key, sub_key, value)
        self.assertEqual(expected_result, given_dict)

        # there is a value before update case
        given_dict = {"a": {"b": {"c"}}}
        key = "a"
        sub_key = "b"
        value = "c2"
        expected_result = {"a": {"b": {"c", "c2"}}}
        add_to_dict_set(given_dict, key, sub_key, value)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "a"
        sub_key = "b"
        value = "c"
        expected_result = {"a": {"b": {"c"}}}
        add_to_dict_set(given_dict, key, sub_key, value)
        self.assertEqual(expected_result, given_dict)

        # there is a None value in level-1 case
        given_dict = {"a": None}
        key = "a"
        sub_key = "b"
        value_set = "c"
        expected_result = {"a": {"b": {"c"}}}
        add_to_dict_set(given_dict, key, sub_key, value_set)
        self.assertEqual(expected_result, given_dict)

    def test_update_to_dict_set(self):
        # lazy load
        from common.utils.dict_coll_util import update_to_dict_set

        # normal case
        given_dict = {}
        key = "a"
        sub_key = "b"
        value_set = {"c"}
        expected_result = {"a": {"b": {"c"}}}
        update_to_dict_set(given_dict, key, sub_key, value_set)
        self.assertEqual(expected_result, given_dict)

        # there is a value before update case
        given_dict = {"a": {"b": {"c"}}}
        key = "a"
        sub_key = "b"
        value_set = {"c2"}
        expected_result = {"a": {"b": {"c", "c2"}}}
        update_to_dict_set(given_dict, key, sub_key, value_set)
        self.assertEqual(expected_result, given_dict)

        # empty case
        given_dict = {}
        key = "a"
        sub_key = "b"
        value_set = {"c"}
        expected_result = {"a": {"b": {"c"}}}
        update_to_dict_set(given_dict, key, sub_key, value_set)
        self.assertEqual(expected_result, given_dict)

        # there is a None value in level-1 case
        given_dict = {"a": None}
        key = "a"
        sub_key = "b"
        value_set = {"c"}
        expected_result = {"a": {"b": {"c"}}}
        update_to_dict_set(given_dict, key, sub_key, value_set)
        self.assertEqual(expected_result, given_dict)
