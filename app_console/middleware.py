"""Console HTTP middleware."""

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden


def _path_exempt_from_console_staff_check(path: str) -> bool:
    """Paths under /console/ that skip staff session checks (separate auth or public)."""
    if path.rstrip("/") == "/console/login":
        return True
    if path == "/console/api/monitoring.json" or path.rstrip("/") == "/console/api/monitoring.json":
        return True
    return False


class ConsoleStaffRequiredMiddleware:
    """
    Require an authenticated staff user for /console/* except login and exempt routes.

    Monitoring JSON export keeps token-based access without Django session.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "APP_CONSOLE_ENABLED", False):
            return self.get_response(request)

        path = request.path or ""
        if not (path == "/console" or path.startswith("/console/")):
            return self.get_response(request)

        if _path_exempt_from_console_staff_check(path):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)

        if not user.is_staff:
            return HttpResponseForbidden("Console access requires an is_staff Django user.")

        return self.get_response(request)
