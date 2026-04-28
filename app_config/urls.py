from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_config.views import ConfigHealthView, ConfigPriQueryView, ConfigPubQueryView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="config-dict"),
    path("health", ConfigHealthView.as_view(), name="config-health"),
    path("pub", ConfigPubQueryView.as_view(), name="config-pub"),
    path("pri", ConfigPriQueryView.as_view(), name="config-pri"),
]
