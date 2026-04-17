import socket
from unittest import TestCase
from unittest.mock import patch

from django.test import override_settings

from common.services.http.outbound_url import (
    OutboundUrlPolicyError,
    sanitize_url_for_log,
    validate_outbound_http_url,
)


class OutboundUrlPolicyTest(TestCase):
    def test_sanitize_url_for_log_strips_query_and_fragment(self):
        self.assertEqual(
            sanitize_url_for_log("https://ex.com/path?token=secret#frag"),
            "https://ex.com/path",
        )

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("ftp://203.0.113.1/")
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("file:///etc/passwd")

    def test_rejects_loopback_ipv4(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://127.0.0.1/")

    def test_rejects_loopback_ipv6(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://[::1]/")

    def test_rejects_private_ipv4(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://10.0.0.1/")

    def test_rejects_metadata_link_local(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://169.254.169.254/latest/")

    def test_allows_documentation_net_literal(self):
        validate_outbound_http_url("http://203.0.113.10/path")

    def test_rejects_userinfo(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://user:pass@203.0.113.1/")

    def test_rejects_localhost_hostname(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://localhost/")

    @patch("common.services.http.outbound_url.socket.getaddrinfo")
    def test_resolved_private_ip_rejected(self, gai_mock):
        gai_mock.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0)),
        ]
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://public-looking.example/")

    @patch("common.services.http.outbound_url.socket.getaddrinfo")
    def test_resolved_public_ip_allowed(self, gai_mock):
        gai_mock.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.20", 0)),
        ]
        validate_outbound_http_url("http://public-looking.example/")

    @override_settings(HTTPX_OUTBOUND_SSRF_RESOLVE_DNS=False)
    def test_hostname_rejected_when_dns_disabled(self):
        with self.assertRaises(OutboundUrlPolicyError):
            validate_outbound_http_url("http://example.com/")
