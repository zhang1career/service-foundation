from unittest import TestCase

from common.components.singleton import Singleton


class OneArgSingleton(Singleton):
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name


class AnotherArgSingleton(Singleton):
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name


class MultiArgSingleton(Singleton):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description


class TestSingleton(TestCase):
    def test_instance_identity(self):
        # normal case
        instance_1 = OneArgSingleton("foo")
        instance_2 = OneArgSingleton("foo")
        instance_3 = OneArgSingleton("bar")
        self.assertIs(instance_1, instance_2)
        self.assertIsNot(instance_1, instance_3)

        # empty case
        instance_4 = OneArgSingleton("")
        instance_5 = OneArgSingleton("")
        self.assertIs(instance_4, instance_5)
        self.assertIsNot(instance_1, instance_4)

        # None case
        instance_6 = OneArgSingleton(None)
        instance_7 = OneArgSingleton(None)
        self.assertIs(instance_6, instance_7)
        self.assertIsNot(instance_1, instance_6)

        # blank case
        instance_8 = OneArgSingleton(" ")
        instance_9 = OneArgSingleton(" ")
        self.assertIs(instance_8, instance_9)
        self.assertIsNot(instance_1, instance_8)
        self.assertIsNot(instance_4, instance_8)
        self.assertIsNot(instance_6, instance_8)

        # multi arg case
        instance_10 = MultiArgSingleton("foo", "a")
        instance_11 = MultiArgSingleton("foo", "a")
        instance_12 = MultiArgSingleton("foo", "b")
        self.assertIs(instance_10, instance_11)
        self.assertIsNot(instance_10, instance_12)

        # multi arg sorted case
        instance_13 = MultiArgSingleton(name="a", description="b")
        instance_14 = MultiArgSingleton(description="b", name="a")
        instance_15 = MultiArgSingleton("a", "b")
        instance_16 = MultiArgSingleton("b", "a")
        self.assertIs(instance_13, instance_14)
        self.assertIsNot(instance_15, instance_16)

        # different class
        instance_17 = AnotherArgSingleton("foo")
        self.assertIsNot(instance_1, instance_17)

        # class functionality
        self.assertEqual(instance_1.get_name(), "foo")
        self.assertEqual(instance_4.get_name(), "")
        self.assertEqual(instance_6.get_name(), None)
        self.assertEqual(instance_8.get_name(), " ")
        self.assertEqual(instance_10.get_name(), "foo")
        self.assertEqual(instance_10.get_description(), "a")
