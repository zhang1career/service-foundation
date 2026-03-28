from unittest import TestCase

from common.utils.dict_util import (
    columns_copy_batch,
    get_by_dict,
    get_multiple_value_dict,
    get_multiple_value_list,
    merge,
    nest_clip,
    set_by_dict,
    sort_and_hash,
)


class DictUtilBoundaryTest(TestCase):
    def test_get_multiple_value_list_empty_dict_returns_empty_list(self):
        self.assertEqual(get_multiple_value_list({}, ["a"]), [])
        self.assertEqual(get_multiple_value_list(None, ["a"]), [])

    def test_get_multiple_value_dict_missing_keys(self):
        result = get_multiple_value_dict({"a": 1, "b": 2}, ["b", "c"])
        self.assertEqual(result, {"b": 2})

    def test_columns_copy_batch(self):
        result = columns_copy_batch([{"a": 1, "b": 2}, {"a": 9}], ["a"])
        self.assertEqual(result, [{"a": 1}, {"a": 9}])

    def test_get_set_by_dict(self):
        target = {}
        key = {"k1": 1, "k2": "x"}
        set_by_dict(target, key, "value")
        self.assertEqual(get_by_dict(target, key), "value")
        self.assertIsNone(get_by_dict(target, {"k1": 2}))

    def test_merge_no_input_and_overwrite(self):
        self.assertEqual(merge(), {})
        self.assertEqual(merge({"a": 1}, {"a": 2, "b": 3}), {"a": 2, "b": 3})

    def test_nest_clip_missing_intermediate_or_non_dict(self):
        source = {"a": {"b": {"c": 1}}, "x": 3}
        self.assertEqual(nest_clip(source, ["a", "b", "z"]), {})
        self.assertEqual(nest_clip({"a": 1}, ["a", "b"]), {})

    def test_sort_and_hash_deterministic(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        self.assertEqual(sort_and_hash(d1), sort_and_hash(d2))
