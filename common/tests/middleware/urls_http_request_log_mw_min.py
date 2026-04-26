"""Minimal URLconf for HttpRequestLogMiddleware tests (resolve → view module)."""

from django.http import HttpResponse
from django.urls import path


def _stub_app_user_view(request):
    return HttpResponse()


# Pretend this view lives in app_user so logging resolves to logger ``app_user``.
_stub_app_user_view.__module__ = "app_user.stub"


urlpatterns = [
    path("api/user/stub/", _stub_app_user_view),
]
