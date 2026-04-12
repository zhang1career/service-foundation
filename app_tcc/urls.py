from django.urls import path

from app_tcc.views.tcc_health_view import TccHealthView
from app_tcc.views.transaction_api_view import (
    TccTransactionBeginView,
    TccTransactionCancelView,
    TccTransactionConfirmView,
    TccTransactionDetailView,
)

urlpatterns = [
    path("health", TccHealthView.as_view(), name="tcc-health"),
    path("transactions/begin", TccTransactionBeginView.as_view(), name="tcc-tx-begin"),
    path("transactions/detail", TccTransactionDetailView.as_view(), name="tcc-tx-detail"),
    path(
        "transactions/<str:global_tx_id>/confirm",
        TccTransactionConfirmView.as_view(),
        name="tcc-tx-confirm",
    ),
    path(
        "transactions/<str:global_tx_id>/cancel",
        TccTransactionCancelView.as_view(),
        name="tcc-tx-cancel",
    ),
]
