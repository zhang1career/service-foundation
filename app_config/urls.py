from django.urls import path

from app_config.views import ConfigHealthView, ConfigPriQueryView, ConfigPubQueryView

urlpatterns = [
    path("health", ConfigHealthView.as_view(), name="config-health"),
    path("pub", ConfigPubQueryView.as_view(), name="config-pub"),
    path("pri", ConfigPriQueryView.as_view(), name="config-pri"),
]
