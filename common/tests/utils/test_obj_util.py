from unittest import TestCase

from common.tests.enums.test_enum import TestEnum


class Test(TestCase):

    def setUp(self):
        pass

    def test_prop_of(self):
        # lazy load
        from common.utils.obj_util import prop_of

        # normal case
        field = "name"
        param = [TestEnum.a, TestEnum.b, TestEnum.c]
        expected_result = ["a", "b", "c"]
        actual_result = prop_of(param, field)
        self.assertEqual(expected_result, actual_result)

        # enum case
        field = "value"
        param = [TestEnum.a, TestEnum.b, TestEnum.c]
        expected_result = [0, 1, 2]
        actual_result = prop_of(param, field)
        self.assertEqual(expected_result, actual_result)

        # empty case
        field = "name"
        param = []
        expected_result = []
        actual_result = prop_of(param, field)
        self.assertEqual(expected_result, actual_result)

        # None case
        field = "name"
        param = None
        expected_result = []
        actual_result = prop_of(param, field)
        self.assertEqual(expected_result, actual_result)

        # None element case
        field = "name"
        param = [TestEnum.a, TestEnum.b, None]
        expected_result = ["a", "b"]
        actual_result = prop_of(param, field)
        self.assertEqual(expected_result, actual_result)


    def test_map_of(self):
        # lazy load
        from common.utils.obj_util import map_of

        # normal case
        func = lambda v: v.name
        param = [TestEnum.a, TestEnum.b, TestEnum.c]
        expected_result = ["a", "b", "c"]
        actual_result = map_of(func, param)
        self.assertEqual(expected_result, actual_result)

        # empty case
        func = lambda v: v.name
        param = []
        expected_result = []
        actual_result = map_of(func, param)
        self.assertEqual(expected_result, actual_result)

        # None case
        func = lambda v: v.name
        param = None
        expected_result = []
        actual_result = map_of(func, param)
        self.assertEqual(expected_result, actual_result)

        # None element case
        func = lambda v: v.name
        param = [TestEnum.a, TestEnum.b, None]
        expected_result = ["a", "b", None]
        actual_result = map_of(func, param)
        self.assertEqual(expected_result, actual_result)

