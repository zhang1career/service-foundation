"""Tests for :func:`maybe_expand_service_discovery_url`."""

from unittest.mock import patch

from django.test import SimpleTestCase

from common.services.service_discovery import maybe_expand_service_discovery_url
from common.utils.service_url_template import ServiceUrlResolutionError


class MaybeExpandServiceDiscoveryUrlTests(SimpleTestCase):
    def test_plain_url_preserves_trailing_slash(self) -> None:
        self.assertEqual(
            maybe_expand_service_discovery_url("  http://a.example/b/  "),
            "http://a.example/b/",
        )

    def test_empty(self) -> None:
        self.assertEqual(maybe_expand_service_discovery_url(""), "")

    @patch(
        "common.services.service_discovery.expand.expand_service_discovery_url",
        return_value="http://h:1/p",
    )
    def test_delegates_to_expand_when_templated(self, m_expand) -> None:
        out = maybe_expand_service_discovery_url("http://{{svc}}/p")
        self.assertEqual(out, "http://h:1/p")
        m_expand.assert_called_once()

    @patch(
        "common.services.service_discovery.expand.expand_service_discovery_url",
        side_effect=ServiceUrlResolutionError("no redis key"),
    )
    def test_propagates_resolution_error(self, _m) -> None:
        with self.assertRaises(ServiceUrlResolutionError):
            maybe_expand_service_discovery_url("http://{{svc}}/p")
