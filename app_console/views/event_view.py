from django.views.generic import TemplateView

from common.consts.query_const import LIMIT_PAGE


class UserEventListConsoleView(TemplateView):
    template_name = "console/event/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["limit_page"] = LIMIT_PAGE
        return context


class UserEventDetailConsoleView(TemplateView):
    template_name = "console/event/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_id"] = int(kwargs.get("event_id"))
        return context


class UserEventEditConsoleView(TemplateView):
    template_name = "console/event/edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_id"] = int(kwargs.get("event_id"))
        return context
