from django.views.generic import TemplateView

from app_user.services.user_service import UserService
from common.consts.query_const import LIMIT_PAGE


class UserListConsoleView(TemplateView):
    template_name = "console/user/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = UserService.list_users(offset=0, limit=LIMIT_PAGE)
        context["users"] = page.get("data") or []
        return context


class UserDetailConsoleView(TemplateView):
    template_name = "console/user/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_id"] = int(kwargs.get("user_id"))
        return context


class UserEditConsoleView(TemplateView):
    template_name = "console/user/edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_id"] = int(kwargs.get("user_id"))
        return context
