"""Tests for common.utils.service_url_template."""

import os
from unittest import TestCase
from unittest.mock import patch

from common.utils.service_url_template import (
    ServiceUrlResolutionError,
    ensure_url_has_no_unresolved_placeholders,
    expand_service_url_from_env,
    resolve_service_host_from_env,
    specify_service_host,
    substitute_url_context_placeholders,
)


class ServiceUrlTemplateTests(TestCase):
    def test_plain_url_unchanged(self):
        self.assertEqual(
            specify_service_host("https://x.example/api", resolve_service_host_from_env),
            "https://x.example/api",
        )

    def test_empty_url(self):
        self.assertEqual(specify_service_host("", resolve_service_host_from_env), "")

    def test_no_placeholder_after_scheme_probe(self):
        # contains "://" but not "://{{"
        self.assertEqual(
            specify_service_host("http://example.com/{{x}}/y", resolve_service_host_from_env),
            "http://example.com/{{x}}/y",
        )

    @patch.dict(os.environ, {"SERVICE_HOST_MY_SVC": "h1:8080"}, clear=False)
    def test_resolves_first_service_segment(self):
        out = specify_service_host(
            "http://{{my-svc}}/api/snowflake/id", resolve_service_host_from_env
        )
        self.assertEqual(out, "http://h1:8080/api/snowflake/id")

    @patch.dict(os.environ, {"SERVICE_HOST_MY_SVC": "h1:8080"}, clear=False)
    def test_replaces_all_matching_braces_for_same_key(self):
        out = specify_service_host(
            "http://{{my-svc}}/p/{{my-svc}}/q", resolve_service_host_from_env
        )
        self.assertEqual(out, "http://h1:8080/p/h1:8080/q")

    @patch.dict(os.environ, {"SERVICE_HOST_MISSING": ""}, clear=False)
    def test_missing_env_raises(self):
        with self.assertRaises(ServiceUrlResolutionError) as ctx:
            resolve_service_host_from_env("missing")
        self.assertIn("SERVICE_HOST_MISSING", str(ctx.exception))

    @patch.dict(os.environ, {"SERVICE_HOST_A": "x:1"}, clear=False)
    def test_custom_resolver_callable(self):
        def fake_resolve(key: str, index: int | None = None) -> str:
            _ = index
            if key == "a":
                return "custom"
            return "other"

        out = specify_service_host("http://{{a}}/v1", fake_resolve)
        self.assertEqual(out, "http://custom/v1")

    @patch.dict(os.environ, {"SERVICE_HOST_SF_SNOWFLAKE": "snow:9000"}, clear=False)
    def test_expand_service_url_from_env_alias(self):
        self.assertEqual(
            expand_service_url_from_env("http://{{sf-snowflake}}/api/snowflake/id"),
            "http://snow:9000/api/snowflake/id",
        )

    def test_substitute_context_empty_url(self):
        self.assertEqual(substitute_url_context_placeholders("", {"a": "1"}), "")

    def test_substitute_context_none_mapping(self):
        self.assertEqual(
            substitute_url_context_placeholders("http://h/p/{{x}}", None),
            "http://h/p/{{x}}",
        )

    def test_substitute_context_replaces_known_only(self):
        out = substitute_url_context_placeholders(
            "http://h/a/{{idem_key}}/b/{{missing}}",
            {"idem_key": "42"},
        )
        self.assertEqual(out, "http://h/a/42/b/{{missing}}")
        with self.assertRaises(ServiceUrlResolutionError) as ctx:
            ensure_url_has_no_unresolved_placeholders(out)
        self.assertIn("missing", str(ctx.exception))

    def test_ensure_no_unresolved_accepts_fully_resolved(self):
        ensure_url_has_no_unresolved_placeholders("http://h/orders/1")

    def test_ensure_rejects_malformed_brace(self):
        with self.assertRaises(ServiceUrlResolutionError) as ctx:
            ensure_url_has_no_unresolved_placeholders("http://h/x{{y")
        self.assertIn("Invalid or incomplete", str(ctx.exception))

    def test_substitute_after_host_expand_chain(self):
        with patch.dict(os.environ, {"SERVICE_HOST_SVC": "api:8080"}, clear=False):
            u = specify_service_host(
                "http://{{svc}}/orders/{{idem_key}}",
                resolve_service_host_from_env,
            )
        out = substitute_url_context_placeholders(u, {"idem_key": "99"})
        self.assertEqual(out, "http://api:8080/orders/99")
        ensure_url_has_no_unresolved_placeholders(out)
