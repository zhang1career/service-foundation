from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_diff(self):
        # lazy load
        from common.utils.set_util import diff

        # normal case
        origin_set = {1, 2, 3}
        target_set = {2, 3, 4}
        expected_result = ({4}, {1})
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # origin_set is None case
        origin_set = None
        target_set = {2, 3, 4}
        expected_result = ({2, 3, 4}, set())
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # target_set is None case
        origin_set = {1, 2, 3}
        target_set = None
        expected_result = (set(), {1, 2, 3})
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # all None case
        origin_set = None
        target_set = None
        expected_result = (set(), set())
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # empty case
        origin_set = set()
        target_set = set()
        expected_result = (set(), set())
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # no diff case
        origin_set = {1, 2, 3}
        target_set = {1, 2, 3}
        expected_result = (set(), set())
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # no intersection case
        origin_set = {1, 2, 3}
        target_set = {4, 5, 6}
        expected_result = ({4, 5, 6}, {1, 2, 3})
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)

        # param isolation case
        origin_set = {1, 2, 3}
        target_set = {2, 3, 4}
        expected_result = ({4}, {1})
        actual_result = diff(origin_set, target_set)
        self.assertEqual(expected_result, actual_result)
        origin_set.remove(1)
        target_set.add(6)
        self.assertEqual({4}, actual_result[0])
        self.assertEqual({1}, actual_result[1])

