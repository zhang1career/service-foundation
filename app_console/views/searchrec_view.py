from django.conf import settings
from django.views.generic import TemplateView


class SearchRecConsoleView(TemplateView):
    template_name = "console/searchrec/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["searchrec_enabled"] = getattr(settings, "APP_SEARCHREC_ENABLED", False)
        context["searchrec_api_base"] = "/api/searchrec"
        return context
