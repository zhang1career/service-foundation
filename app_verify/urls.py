from django.urls import path

from app_verify.views import VerifyRequestView, VerifyCheckView, RegListCreateView, RegDetailView


urlpatterns = [
    path("regs", RegListCreateView.as_view(), name="verify-reg-list-create"),
    path("regs/<int:reg_id>", RegDetailView.as_view(), name="verify-reg-detail"),
    path("request", VerifyRequestView.as_view(), name="verify-request"),
    path("check", VerifyCheckView.as_view(), name="verify-check"),
]
