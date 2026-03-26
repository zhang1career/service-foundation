from django.urls import path

from app_searchrec.views import (
    SearchRecHealthView,
    SearchRecIndexUpsertView,
    SearchRecRankView,
    SearchRecRecommendView,
    SearchRecSearchView,
)

urlpatterns = [
    path("health", SearchRecHealthView.as_view(), name="searchrec-health"),
    path("index/upsert", SearchRecIndexUpsertView.as_view(), name="searchrec-index-upsert"),
    path("search", SearchRecSearchView.as_view(), name="searchrec-search"),
    path("recommend", SearchRecRecommendView.as_view(), name="searchrec-recommend"),
    path("rank", SearchRecRankView.as_view(), name="searchrec-rank"),
]
