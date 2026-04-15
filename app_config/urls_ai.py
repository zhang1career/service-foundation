from django.urls import path

from app_config.views import ConfigPriQueryView

urlpatterns = [
    path("pri", ConfigPriQueryView.as_view(), name="config-pri"),
]
