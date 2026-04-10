import json

from django.conf import settings
from django.views.generic import TemplateView

from app_console.views.reg_console_view import RegConsoleView
from app_searchrec.services.reg_service import SearchRecRegService


def _searchrec_api_debug_example_payloads(access_key: str) -> dict[str, str]:
    """Compact JSON for API debug textareas; access_key is CONSOLE_SEARCHREC_ACCESS_KEY as-is."""
    ak = access_key
    return {
        "upsert": json.dumps(
            {
                "access_key": ak,
                "documents": [
                    {
                        "id": "doc_1",
                        "title": "Hello Search",
                        "content": "search and recommend",
                        "tags": ["search"],
                        "score_boost": 1.0,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        "search": json.dumps(
            {
                "access_key": ak,
                "query": "search recommend",
                "top_k": 10,
                "preferred_tags": ["search"],
            },
            ensure_ascii=False,
        ),
        "recommend": json.dumps(
            {
                "access_key": ak,
                "user_profile": {
                    "preferred_tags": ["search"],
                    "recent_queries": ["hybrid search"],
                    "affinity_boost": 1.1,
                },
                "top_k": 10,
            },
            ensure_ascii=False,
        ),
        "rank": json.dumps(
            {
                "access_key": ak,
                "strategy": "hybrid",
                "candidates": [
                    {
                        "id": "a",
                        "base_score": 0.8,
                        "ctr_score": 0.2,
                        "freshness_score": 0.3,
                    },
                    {
                        "id": "b",
                        "base_score": 0.6,
                        "ctr_score": 0.7,
                        "freshness_score": 0.1,
                    },
                ],
            },
            ensure_ascii=False,
        ),
    }


class SearchRecRegConsoleView(RegConsoleView):
    """搜索推荐 — 使用方（reg）管理。"""

    template_name = "console/searchrec/reg_list.html"
    reg_service = SearchRecRegService


class SearchRecConsoleView(TemplateView):
    """SearchRec API 调试页。"""

    template_name = "console/searchrec/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["searchrec_enabled"] = getattr(settings, "APP_SEARCHREC_ENABLED", False)
        context["searchrec_api_base"] = "/api/searchrec"
        context["searchrec_examples"] = _searchrec_api_debug_example_payloads(
            settings.CONSOLE_SEARCHREC_ACCESS_KEY
        )
        return context
