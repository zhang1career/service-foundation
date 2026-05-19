"""控制台/运维 JSON API：枚举字典与词库管理，挂载于 ``/admin/textmod/``（见 ``service_foundation.urls``）。"""
from django.urls import path

from common.views.dict_codes_view import DictCodesView

from app_textmod.views.lexicon_views import LexiconEntriesCreateView, LexiconListCreateView, LexiconPublishView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="textmod-dict"),
    path("lexicons", LexiconListCreateView.as_view(), name="textmod-lexicon-list-create"),
    path("lexicons/<int:lexicon_id>/entries", LexiconEntriesCreateView.as_view(), name="textmod-lexicon-entries"),
    path("lexicons/<int:lexicon_id>/publish", LexiconPublishView.as_view(), name="textmod-lexicon-publish"),
]
