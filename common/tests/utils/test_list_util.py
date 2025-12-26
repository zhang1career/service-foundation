from unittest import TestCase


class Test(TestCase):

    def setUp(self):
        pass

    def test_check_empty(self):
        # lazy load
        from common.utils.list_util import check_empty

        # normal case
        origin_list = ["a", "b"]
        result = check_empty(origin_list)
        self.assertFalse(result)

        # empty case
        origin_list = []
        result = check_empty(origin_list)
        self.assertTrue(result)

        # None case
        origin_list = None
        result = check_empty(origin_list)
        self.assertTrue(result)


    def test_list_first_element(self):
        # lazy load
        from common.utils.list_util import list_first_element

        result = list_first_element(['c', 'a', 'b'])
        self.assertEqual('a', result)

    def test_column_of(self):
        # lazy load
        from common.utils.list_util import column_of

        # normal case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = "name"
        expected_result = ["a", "b"]
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field not in object case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2}]
        origin_field = "name"
        expected_result = ["a"]
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field not in any objects case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = "content"
        expected_result = []
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field is None case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = None
        expected_result = []
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # list is None case
        origin_list = None
        origin_field = "name"
        expected_result = []
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # all None case
        origin_list = None
        origin_field = None
        expected_result = []
        actual_result = column_of(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)


    def test_index_by(self):
        # lazy load
        from common.utils.list_util import index_by

        # normal case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = "id"
        expected_result = {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field not in object case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2}]
        origin_field = "name"
        expected_result = {"a": {"id": 1, "name": "a"}}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field not in any objects case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = "content"
        expected_result = {}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # field is None case
        origin_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        origin_field = None
        expected_result = {}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # list is None case
        origin_list = None
        origin_field = "id"
        expected_result = {}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)

        # all None case
        origin_list = None
        origin_field = None
        expected_result = {}
        actual_result = index_by(origin_list, origin_field)
        self.assertEqual(expected_result, actual_result)


    def test_cartisan_product(self):
        # lazy load
        from common.utils.list_util import cartesian_product

        # normal case
        argument1_list = ['a', 'b', 'c']
        argument2_list = ['1', '2', '3']
        expected_result = [('a', '1'), ('a', '2'), ('a', '3'),
                           ('b', '1'), ('b', '2'), ('b', '3'),
                           ('c', '1'), ('c', '2'), ('c', '3')]
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # argument1 is None case
        argument1_list = None
        argument2_list = ['1', '2', '3']
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # argument2 is None case
        argument1_list = ['a', 'b', 'c']
        argument2_list = None
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # all None case
        argument1_list = None
        argument2_list = None
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # argument1 is empty case
        argument1_list = []
        argument2_list = ['1', '2', '3']
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # argument2 is empty case
        argument1_list = ['a', 'b', 'c']
        argument2_list = []
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)

        # all empty case
        argument1_list = []
        argument2_list = []
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)


    def test_cartisan_product_with_empty_argument(self):
        # lazy load
        from common.utils.list_util import cartesian_product

        argument1_list = ['a', 'b', 'c']
        argument2_list = []
        expected_result = []
        actual_result = cartesian_product(argument1_list, argument2_list)
        self.assertEqual(expected_result, actual_result)
    
    def test_append_and_unique_list(self):
        # lazy load
        from common.utils.list_util import append_and_unique_list

        # normal case
        origin_list1 = ["a", "b"]
        origin_append1 = "a"
        origin_append2 = "c"
        expected_result = ["a", "b", "c"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # list empty case
        origin_list1 = []
        origin_append1 = "a"
        origin_append2 = "c"
        expected_result = ["a", "c"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # append empty case
        origin_list1 = ["a", "b"]
        origin_append1 = "a"
        origin_append2 = ""
        expected_result = ["a", "b"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # list and appends empty case
        origin_list1 = []
        origin_append1 = ""
        origin_append2 = ""
        expected_result = []
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # list None case
        origin_list1 = None
        origin_append1 = "a"
        origin_append2 = "c"
        expected_result = ["a", "c"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # append None case
        origin_list1 = ["a", "b"]
        origin_append1 = "a"
        origin_append2 = None
        expected_result = ["a", "b"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # appends all None case
        origin_list1 = ["a", "b"]
        origin_append1 = None
        origin_append2 = None
        expected_result = ["a", "b"]
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # list and appends all None case
        origin_list1 = None
        origin_append1 = None
        origin_append2 = None
        expected_result = []
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(expected_result, actual_result)

        # param isolation case
        origin_list1 = ["a", "b"]
        origin_append1 = "a"
        origin_append2 = "c"
        actual_result = append_and_unique_list(origin_list1, origin_append1, origin_append2)
        self.assertEqual(["a", "b"], origin_list1)
