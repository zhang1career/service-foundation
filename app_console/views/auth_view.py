"""Django session login/logout for the operations console."""

from django.http import HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView


class ConsoleLoginView(LoginView):
    template_name = "console/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "此账号不是运维人员（需要 is_staff）。")
            return self.form_invalid(form)
        return super().form_valid(form)


class ConsoleLogoutView(LogoutView):
    http_method_names = ["post", "options"]
