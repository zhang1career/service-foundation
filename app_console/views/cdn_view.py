"""CDN control views for app_console."""
from django.conf import settings
from django.views.generic import TemplateView

CDN_API_BASE = "/api/cdn/2020-05-31"


class CdnDistributionListView(TemplateView):
    """List CDN distributions with create capability."""
    template_name = "console/cdn/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cdn_api_base"] = CDN_API_BASE
        context["cdn_enabled"] = getattr(settings, "APP_CDN_ENABLED", False)
        return context


class CdnDistributionDetailView(TemplateView):
    """CDN distribution detail with invalidations and create invalidation."""
    template_name = "console/cdn/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["distribution_id"] = kwargs.get("distribution_id", "")
        context["cdn_api_base"] = CDN_API_BASE
        return context
