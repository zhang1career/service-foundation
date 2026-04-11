"""
ASGI config for service_foundation project.

Exposes ``application`` for HTTP (Django) and, when ``APP_KEEPCON_ENABLED``,
WebSocket (Channels) on ``/ws/keepcon/``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_foundation.settings")

django_asgi_app = get_asgi_application()

from django.conf import settings  # noqa: E402

if getattr(settings, "APP_KEEPCON_ENABLED", False):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter

    from app_keepcon.routing import websocket_urlpatterns

    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        }
    )
else:
    application = django_asgi_app
