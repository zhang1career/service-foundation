from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_notice.views import NoticeSendView, RegListCreateView, RegDetailView


urlpatterns = [
    path("dict", DictCodesView.as_view(), name="notice-dict"),
    path("regs", RegListCreateView.as_view(), name="notice-reg-list-create"),
    path("regs/<int:reg_id>", RegDetailView.as_view(), name="notice-reg-detail"),
    path("send", NoticeSendView.as_view(), name="notice-send"),
]
