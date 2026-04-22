from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_searchrec.views import (
    SearchRecHealthView,
    SearchRecIndexUpsertView,
    SearchRecRankView,
    SearchRecRecommendView,
    SearchRecSearchView,
)

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="searchrec-dict"),
    path("health", SearchRecHealthView.as_view(), name="searchrec-health"),
    path("index", SearchRecIndexUpsertView.as_view(), name="searchrec-index"),
    path("search", SearchRecSearchView.as_view(), name="searchrec-search"),
    path("recommend", SearchRecRecommendView.as_view(), name="searchrec-recommend"),
    path("rank", SearchRecRankView.as_view(), name="searchrec-rank"),
]
