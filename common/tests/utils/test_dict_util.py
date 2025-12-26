from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_check_empty(self):
        # lazy load
        from common.utils.dict_util import check_empty

        # normal case
        given_param = {"foo": "bar"}
        self.assertFalse(check_empty(given_param))

        # empty case
        given_param = {}
        self.assertTrue(check_empty(given_param))

        # None case
        given_param = None
        self.assertTrue(check_empty(given_param))

    def test_get_first_key(self):
        # lazy load
        from common.utils.dict_util import get_first_key

        # normal case
        given_param = {"foo": "bar", "baz": "qux"}
        expected_result = "foo"
        actual_result = get_first_key(given_param)
        self.assertEqual(expected_result, actual_result)

        # empty case
        given_param = {}
        expected_result = None
        actual_result = get_first_key(given_param)
        self.assertEqual(expected_result, actual_result)

        # None case
        given_param = None
        expected_result = None
        actual_result = get_first_key(given_param)
        self.assertEqual(expected_result, actual_result)

    def test_get_key_list(self):
        # lazy load
        from common.utils.dict_util import get_key_list

        # normal case
        given_param = {"foo": "bar", "baz": "qux"}
        expected_result = ["foo", "baz"]
        actual_result = get_key_list(given_param)
        self.assertEqual(expected_result, actual_result)

        # empty case
        given_param = {}
        expected_result = []
        actual_result = get_key_list(given_param)
        self.assertEqual(expected_result, actual_result)

        # None case
        given_param = None
        expected_result = []
        actual_result = get_key_list(given_param)
        self.assertEqual(expected_result, actual_result)

    def test_get_value_list(self):
        # lazy load
        from common.utils.dict_util import get_value_list

        # normal case
        given_param = {"foo": "bar", "baz": "qux"}
        expected_result = ["bar", "qux"]
        actual_result = get_value_list(given_param)
        self.assertEqual(expected_result, actual_result)

        # some None case
        given_param = {"foo": "bar", "baz": None}
        expected_result = ["bar", None]
        actual_result = get_value_list(given_param)
        self.assertEqual(expected_result, actual_result)

        # empty case
        given_param = {}
        expected_result = []
        actual_result = get_value_list(given_param)
        self.assertEqual(expected_result, actual_result)

        # None case
        given_param = None
        expected_result = []
        actual_result = get_value_list(given_param)
        self.assertEqual(expected_result, actual_result)

    def test_get_multiple_values(self):
        # lazy load
        from common.utils.dict_util import get_multiple_value_list

        # normal case
        given_param = {"foo": "bar", "baz": "qux"}
        given_keys = ["foo", "baz"]
        expected_result = ["bar", "qux"]
        actual_result = get_multiple_value_list(given_param, given_keys)
        self.assertEqual(expected_result, actual_result)

        # some None case
        given_param = {"foo": "bar", "baz": None}
        given_keys = ["foo", "baz"]
        expected_result = ["bar", None]
        actual_result = get_multiple_value_list(given_param, given_keys)
        self.assertEqual(expected_result, actual_result)

        # some absent case
        given_param = {"foo": "bar", "baz": "qux"}
        given_keys = ["foo", "baa"]
        expected_result = ["bar"]
        actual_result = get_multiple_value_list(given_param, given_keys)
        self.assertEqual(expected_result, actual_result)

        # empty case
        given_param = {}
        given_keys = ["foo", "baz"]
        expected_result = None
        actual_result = get_multiple_value_list(given_param, given_keys)
        self.assertEqual(expected_result, actual_result)

        # None case
        given_param = None
        given_keys = ["foo", "baz"]
        expected_result = None
        actual_result = get_multiple_value_list(given_param, given_keys)
        self.assertEqual(expected_result, actual_result)

    def test_dict_first_value(self):
        # lazy load
        from common.utils.dict_util import dict_first_value

        result = dict_first_value({"c": 3, "a": 1, "b": 2})
        self.assertEqual(1, result)

    def test_columns_copy(self):
        # lazy load
        from common.utils.dict_util import columns_copy

        original_dict = {
            "name": "John Doe",
            "age": 30,
            "gender": "Male",
            "occupation": "Software Developer"
        }
        columns_to_copy = ["name", "occupation"]
        new_dict = columns_copy(original_dict, columns_to_copy)
        print(new_dict)

    def test_invert(self):
        # lazy load
        from common.utils.dict_util import invert

        argument = {1: "a", 2: "b"}
        expected_result = {"a": 1, "b": 2}
        actual_result = invert(argument)

        self.assertEqual(expected_result, actual_result)

    def test_dict_by(self):
        # lazy load
        from common.utils.dict_util import dict_by

        # normal case
        given_dict = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        key = "b"
        expected_result = {2: {"a": 1, "b": 2}, 3: {"b": 3, "c": 4}}
        actual_result = dict_by(given_dict, key)
        self.assertEqual(expected_result, actual_result)

        # key not in any objects case
        given_dict = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        key = "d"
        expected_result = {}
        actual_result = dict_by(given_dict, key)
        self.assertEqual(expected_result, actual_result)

        # key is None case
        given_dict = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        key = None
        expected_result = {}
        actual_result = dict_by(given_dict, key)
        self.assertEqual(expected_result, actual_result)

        # given_dict is None case
        given_dict = None
        key = "b"
        expected_result = {}
        actual_result = dict_by(given_dict, key)
        self.assertEqual(expected_result, actual_result)

        # all None case
        given_dict = None
        key = None
        expected_result = {}
        actual_result = dict_by(given_dict, key)
        self.assertEqual(expected_result, actual_result)

    def test_nest_clip(self):
        # lazy load
        from common.utils.dict_util import nest_clip

        # normal case
        given_dict = {
            "a": {
                "b": {
                    "c": 1,
                    "d": 2
                },
                "e": 3
            },
            "f": 4
        }
        given_key_list = ["a", "b", "c"]
        expected_result = {"a": {"b": {"c": 1}}}
        actual_result = nest_clip(given_dict, given_key_list)
        self.assertEqual(expected_result, actual_result)

        # key not in dict case
        given_dict = {
            "a": {
                "b": {
                    "c": 1,
                    "d": 2
                },
                "e": 3
            },
            "f": 4
        }
        given_key_list = ["a", "b", "g"]
        expected_result = {}
        actual_result = nest_clip(given_dict, given_key_list)
        self.assertEqual(expected_result, actual_result)

        # key is None case
        given_dict = {
            "a": {
                "b": {
                    "c": 1,
                    "d": 2
                },
                "e": 3
            },
            "f": 4
        }
        given_key_list = None
        expected_result = {}
        actual_result = nest_clip(given_dict, given_key_list)
        self.assertEqual(expected_result, actual_result)

        # given_dict is None case
        given_dict = None
        given_key_list = ["a", "b", "c"]
        expected_result = {}
        actual_result = nest_clip(given_dict, given_key_list)
        self.assertEqual(expected_result, actual_result)

        # all None case
        given_dict = None
        given_key_list = None
        expected_result = {}
        actual_result = nest_clip(given_dict, given_key_list)
        self.assertEqual(expected_result, actual_result)

    def test_sort_and_hash(self):
        # lazy load
        from common.utils.dict_util import sort_and_hash

        # normal case
        given_dict = {"a": 1, "b": 2}
        expected_result = ({"a": 1, "b": 2}, "e338569978c20c19af9ac8cb81b86482")
        actual_result = sort_and_hash(given_dict)
        self.assertEqual(expected_result, actual_result)

        # disordered case
        given_dict = {"b": 2, "a": 1}
        expected_result = ({"a": 1, "b": 2}, "e338569978c20c19af9ac8cb81b86482")
        actual_result = sort_and_hash(given_dict)
        self.assertEqual(expected_result, actual_result)

        # nested list case
        given_dict = {"b": 2, "a": [3, 1]}
        actual_result = sort_and_hash(given_dict)
        expected_dict = {"a": [3, 1], "b": 2}
        expected_result = sort_and_hash(expected_dict)
        self.assertEqual(expected_result, actual_result)

        # empty case
        given_dict = {}
        expected_result = ({}, "")
        actual_result = sort_and_hash(given_dict)
        self.assertEqual(expected_result, actual_result)

        # None case
        given_dict = None
        expected_result = ({}, "")
        actual_result = sort_and_hash(given_dict)
        self.assertEqual(expected_result, actual_result)
