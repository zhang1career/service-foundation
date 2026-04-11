from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_notice.views import NoticeRecordResendView, NoticeSendView, RegListCreateView, RegDetailView
from app_notice.views.health_view import NoticeHealthView


urlpatterns = [
    path("dict", DictCodesView.as_view(), name="notice-dict"),
    path("health", NoticeHealthView.as_view(), name="notice-health"),
    path("regs", RegListCreateView.as_view(), name="notice-reg-list-create"),
    path("regs/<int:reg_id>", RegDetailView.as_view(), name="notice-reg-detail"),
    path("send", NoticeSendView.as_view(), name="notice-send"),
    path(
        "records/<int:notice_id>/send",
        NoticeRecordResendView.as_view(),
        name="notice-record-send",
    ),
]
