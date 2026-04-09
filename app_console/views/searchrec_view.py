from django.conf import settings
from django.views.generic import TemplateView

from app_console.views.reg_console_view import RegConsoleView
from app_searchrec.services.reg_service import SearchRecRegService


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
        return context
