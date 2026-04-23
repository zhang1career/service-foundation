from __future__ import annotations

from django.test import SimpleTestCase

from common.services.service_discovery.service_uri_list import parse_comma_separated, pick_instance


class ServiceUriListTests(SimpleTestCase):
    def test_parse_trims_and_skips_empty(self) -> None:
        self.assertEqual(
            parse_comma_separated(" a , , b , "),
            ["a", "b"],
        )

    def test_pick_indexed(self) -> None:
        self.assertEqual(pick_instance(["x", "y", "z"], 1), "y")
        self.assertEqual(pick_instance(["x", "y", "z"], -1), "z")
