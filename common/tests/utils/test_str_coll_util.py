from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_sort_and_hash(self):
        # lazy load
        from common.utils.string_coll_util import sort_and_hash

        # normal case
        given_list = ["b", "a"]
        expected_result = (["a", "b"], "187ef4436122d1cc2f40dc2b92f0eba0")
        self.assertEqual(expected_result, sort_and_hash(given_list))

        # empty case
        given_list = []
        expected_result = ([], "d41d8cd98f00b204e9800998ecf8427e")
        self.assertEqual(expected_result, sort_and_hash(given_list))

        # one element case
        given_list = ["a"]
        expected_result = (["a"], "0cc175b9c0f1b6a831c399e269772661")
        self.assertEqual(expected_result, sort_and_hash(given_list))

        # multiple elements case
        given_list = ["b", "a", "c"]
        expected_result = (["a", "b", "c"], "900150983cd24fb0d6963f7d28e17f72")
        self.assertEqual(expected_result, sort_and_hash(given_list))

        # order elements case
        asc_list = ["a", "b"]
        dasc_list = ["b", "a"]
        self.assertEqual(sort_and_hash(asc_list), sort_and_hash(dasc_list))
