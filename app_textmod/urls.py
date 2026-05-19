from django.urls import path

from common.views.dict_codes_view import DictCodesView

from app_textmod.views.health_view import TextmodHealthView
from app_textmod.views.lexicon_views import LexiconEntriesCreateView, LexiconListCreateView, LexiconPublishView
from app_textmod.views.scan_view import TextmodScanView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="textmod-dict"),
    path("health", TextmodHealthView.as_view(), name="textmod-health"),
    path("scan", TextmodScanView.as_view(), name="textmod-scan"),
    path("lexicons", LexiconListCreateView.as_view(), name="textmod-lexicon-list-create"),
    path("lexicons/<int:lexicon_id>/entries", LexiconEntriesCreateView.as_view(), name="textmod-lexicon-entries"),
    path("lexicons/<int:lexicon_id>/publish", LexiconPublishView.as_view(), name="textmod-lexicon-publish"),
]
