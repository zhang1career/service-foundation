from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase

from common.annotations import http_client_cache as http_client_cache_module
from common.annotations.http_client_cache import (
    apply_http_client_cache_headers,
    http_response_client_cache,
)


class ApplyHttpClientCacheHeadersTests(SimpleTestCase):
    def test_sets_max_age_and_expires(self):
        response = HttpResponse("ok")
        apply_http_client_cache_headers(response, 60)
        self.assertIn("max-age=60", response["Cache-Control"])
        self.assertTrue(response["Expires"])

    def test_negative_max_age_raises(self):
        response = HttpResponse()
        with self.assertRaises(ValueError):
            apply_http_client_cache_headers(response, -1)


class HttpResponseClientCacheDecoratorTests(SimpleTestCase):
    def test_uses_settings_when_no_explicit_ttl(self):
        @http_response_client_cache()
        def view(_request):
            return HttpResponse("x")

        with patch.object(
                http_client_cache_module,
                "settings",
                SimpleNamespace(HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS=10),
        ):
            response = view(None)
        self.assertIn("max-age=10", response["Cache-Control"])

    def test_explicit_ttl_overrides_setting(self):
        @http_response_client_cache(99)
        def view(_request):
            return HttpResponse("x")

        with patch.object(
                http_client_cache_module,
                "settings",
                SimpleNamespace(HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS=10),
        ):
            response = view(None)
        self.assertIn("max-age=99", response["Cache-Control"])

    def test_bare_decorator_without_call_parens(self):
        @http_response_client_cache
        def view(_request):
            return HttpResponse("x")

        with patch.object(
                http_client_cache_module,
                "settings",
                SimpleNamespace(HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS=7),
        ):
            response = view(None)
        self.assertIn("max-age=7", response["Cache-Control"])

    def test_zero_ttl_falls_back_to_setting(self):
        @http_response_client_cache(0)
        def view(_request):
            return HttpResponse("x")

        with patch.object(
                http_client_cache_module,
                "settings",
                SimpleNamespace(HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS=42),
        ):
            response = view(None)
        self.assertIn("max-age=42", response["Cache-Control"])

    def test_dispatch_style_extra_args(self):
        @http_response_client_cache()
        def dispatch(_self, _request):
            return HttpResponse("x")

        with patch.object(
                http_client_cache_module,
                "settings",
                SimpleNamespace(HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS=10),
        ):
            response = dispatch(object(), None)
        self.assertIn("max-age=10", response["Cache-Control"])

    def test_non_int_first_arg_raises(self):
        bad: object = "nope"
        with self.assertRaises(TypeError):
            http_response_client_cache(bad)
