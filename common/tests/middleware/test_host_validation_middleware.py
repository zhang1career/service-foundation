from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from common.middleware.host_validation_middleware import HostValidationMiddleware


class HostValidationMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_noop_when_http_host_empty(self):
        calls = []

        def get_response(request):
            calls.append(request)
            return HttpResponse("ok")

        mw = HostValidationMiddleware(get_response)
        req = self.factory.get("/")
        del req.META["HTTP_HOST"]
        resp = mw(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(calls[0].META.get("HTTP_HOST"), "")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_normalizes_short_hostname_to_localhost_with_port(self):
        def get_response(request):
            self.assertEqual(request.META["HTTP_HOST"], "localhost:8000")
            return HttpResponse("ok")

        mw = HostValidationMiddleware(get_response)
        req = self.factory.get("/", HTTP_HOST="serv_fd:8000")
        mw(req)

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_sets_server_name_localhost_when_present(self):
        def get_response(request):
            return HttpResponse("ok")

        mw = HostValidationMiddleware(get_response)
        req = self.factory.get("/", HTTP_HOST="svc:9000")
        req.META["SERVER_NAME"] = "svc"
        mw(req)
        self.assertEqual(req.META["HTTP_HOST"], "localhost:9000")
        self.assertEqual(req.META["SERVER_NAME"], "localhost")

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_does_not_change_host_when_not_star(self):
        def get_response(request):
            return HttpResponse("ok")

        mw = HostValidationMiddleware(get_response)
        req = self.factory.get("/", HTTP_HOST="short:8000")
        mw(req)
        self.assertEqual(req.META["HTTP_HOST"], "short:8000")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_skips_localhost_style_hostnames(self):
        def get_response(request):
            return HttpResponse("ok")

        mw = HostValidationMiddleware(get_response)
        req = self.factory.get("/", HTTP_HOST="localhost:3000")
        mw(req)
        self.assertEqual(req.META["HTTP_HOST"], "localhost:3000")
