from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_keepcon.views.keepcon_api_view import KeepconHealthView, KeepconInternalDispatchView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="keepcon-dict"),
    path("health", KeepconHealthView.as_view(), name="keepcon-health"),
    path(
        "internal/messages",
        KeepconInternalDispatchView.as_view(),
        name="keepcon-internal-messages",
    ),
]
