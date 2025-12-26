from django.urls import path

from app_snowflake.views.snowflake_view import SnowflakeDetailView

urlpatterns = [
    path("id", SnowflakeDetailView.as_view()),
]
