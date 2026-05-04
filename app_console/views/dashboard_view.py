import json

from django import get_version
from django.conf import settings
from django.views.generic import TemplateView

from app_console.catalog import build_apps_config_list


class DashboardView(TemplateView):
    template_name = "console/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["django_version"] = get_version()
        context["monitoring_refresh_ms"] = int(getattr(settings, "CONSOLE_MONITORING_REFRESH_MS", 0) or 0)

        apps_config = build_apps_config_list(settings)
        context["apps_config_json"] = json.dumps(apps_config, ensure_ascii=False)
        return context
