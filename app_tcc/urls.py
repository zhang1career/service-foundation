from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_tcc.views.tcc_health_view import TccHealthView
from app_tcc.views.transaction_api_view import (
    TccTransactionBeginView,
    TccTransactionCancelView,
    TccTransactionConfirmView,
    TccTransactionDetailView,
)
from common.views.xxl_job_view import XxlJobBeatView, XxlJobKillView, XxlJobRunView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="tcc-dict"),
    path("health", TccHealthView.as_view(), name="tcc-health"),
    path("xxl-job/beat", XxlJobBeatView.as_view(), name="tcc-xxl-beat"),
    path("xxl-job/run", XxlJobRunView.as_view(), name="tcc-xxl-run"),
    path("xxl-job/kill", XxlJobKillView.as_view(), name="tcc-xxl-kill"),
    path(
        "tx/<str:idem_key>/confirm",
        TccTransactionConfirmView.as_view(),
        name="tcc-tx-confirm",
    ),
    path(
        "tx/<str:idem_key>/cancel",
        TccTransactionCancelView.as_view(),
        name="tcc-tx-cancel",
    ),
    path("tx", TccTransactionBeginView.as_view(), name="tcc-tx-begin"),
    path("tx/<str:idem_key>", TccTransactionDetailView.as_view(), name="tcc-tx-detail"),
]
