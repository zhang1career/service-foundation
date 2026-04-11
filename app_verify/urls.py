from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_verify.views import VerifyRequestView, VerifyCheckView, RegListCreateView, RegDetailView
from app_verify.views.health_view import VerifyHealthView


urlpatterns = [
    path("dict", DictCodesView.as_view(), name="verify-dict"),
    path("health", VerifyHealthView.as_view(), name="verify-health"),
    path("regs", RegListCreateView.as_view(), name="verify-reg-list-create"),
    path("regs/<int:reg_id>", RegDetailView.as_view(), name="verify-reg-detail"),
    path("request", VerifyRequestView.as_view(), name="verify-request"),
    path("check", VerifyCheckView.as_view(), name="verify-check"),
]
