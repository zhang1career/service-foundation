from django.test import SimpleTestCase

from app_searchrec.tags_csv import join_tags_csv, parse_tags_csv


class TestTagsCsv(SimpleTestCase):
    def test_parse_empty(self):
        self.assertEqual(parse_tags_csv(""), [])
        self.assertEqual(parse_tags_csv("   "), [])

    def test_parse_splits_and_trims(self):
        self.assertEqual(parse_tags_csv("a,b,c"), ["a", "b", "c"])
        self.assertEqual(parse_tags_csv(" a , b "), ["a", "b"])

    def test_join_round_trip(self):
        self.assertEqual(join_tags_csv(["a", "b"]), "a,b")
        self.assertEqual(join_tags_csv([]), "")
        self.assertEqual(parse_tags_csv(join_tags_csv(["x", "y"])), ["x", "y"])
