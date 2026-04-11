from django.urls import path

from app_config.views import ConfigHealthView, ConfigQueryView

urlpatterns = [
    path("health", ConfigHealthView.as_view(), name="config-health"),
    path("get", ConfigQueryView.as_view(), name="config-get"),
]
