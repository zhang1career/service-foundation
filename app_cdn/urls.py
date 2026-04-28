"""
CDN URL configuration - CloudFront API compatible paths

API version prefix: 2020-05-31 (matches CloudFront API)
Content delivery: /d/{distribution_id}/{path}
"""
from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_cdn.views.content_delivery_view import ContentDeliveryView
from app_cdn.views.cdn_view import (
    DistributionConfigView,
    DistributionDetailView,
    DistributionListView,
    InvalidationDetailView,
    InvalidationListView,
)

# CloudFront API style paths
urlpatterns = [
    path("dict", DictCodesView.as_view(), name="cdn-dict"),
    # Content delivery (proxy + cache)
    path(
        "d/<str:distribution_id>/",
        ContentDeliveryView.as_view(),
        name="cdn-content-delivery-root",
    ),
    path(
        "d/<str:distribution_id>/<path:path>",
        ContentDeliveryView.as_view(),
        name="cdn-content-delivery",
    ),
    # Distribution
    path("distribution", DistributionListView.as_view(), name="cdn-list-distributions"),
    path(
        "distribution/<str:distribution_id>",
        DistributionDetailView.as_view(),
        name="cdn-distribution-detail",
    ),
    path(
        "distribution/<str:distribution_id>/config",
        DistributionConfigView.as_view(),
        name="cdn-distribution-config",
    ),
    # Invalidation
    path(
        "distribution/<str:distribution_id>/invalidation",
        InvalidationListView.as_view(),
        name="cdn-list-invalidations",
    ),
    path(
        "distribution/<str:distribution_id>/invalidation/<str:invalidation_id>",
        InvalidationDetailView.as_view(),
        name="cdn-invalidation-detail",
    ),
]
