from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_snowflake.views.snowflake_view import SnowflakeDetailView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="snowflake-dict"),
    path("id", SnowflakeDetailView.as_view()),
]
