from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_tuple_to_list(self):
        # lazy load
        from common.utils.map_util import tuple_to_list

        # normal case
        param = (1, 2, 3)
        expected_result = [1, 2, 3]
        actual_result = tuple_to_list(param)
        self.assertEqual(expected_result, actual_result)

        # empty case
        param = ()
        expected_result = []
        actual_result = tuple_to_list(param)
        self.assertEqual(expected_result, actual_result)

        # None case
        param = None
        expected_result = []
        actual_result = tuple_to_list(param)
        self.assertEqual(expected_result, actual_result)

        # None element case
        param = (1, 2, None)
        expected_result = [1, 2, None]
        actual_result = tuple_to_list(param)
        self.assertEqual(expected_result, actual_result)
