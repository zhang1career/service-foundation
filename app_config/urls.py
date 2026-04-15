from django.urls import path

from app_config.views import ConfigHealthView, ConfigPubQueryView

urlpatterns = [
    path("health", ConfigHealthView.as_view(), name="config-health"),
    path("pub", ConfigPubQueryView.as_view(), name="config-pub"),
]
