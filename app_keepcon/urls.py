from django.urls import path

from app_keepcon.views.keepcon_api_view import KeepconHealthView, KeepconInternalDispatchView

urlpatterns = [
    path("health", KeepconHealthView.as_view(), name="keepcon-health"),
    path(
        "internal/messages",
        KeepconInternalDispatchView.as_view(),
        name="keepcon-internal-messages",
    ),
]
