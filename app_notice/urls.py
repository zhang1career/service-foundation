from django.urls import path

from app_notice.views import NoticeSendView, RegListCreateView, RegDetailView


urlpatterns = [
    path("regs", RegListCreateView.as_view(), name="notice-reg-list-create"),
    path("regs/<int:reg_id>", RegDetailView.as_view(), name="notice-reg-detail"),
    path("send", NoticeSendView.as_view(), name="notice-send"),
]
