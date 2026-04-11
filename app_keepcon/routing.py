from django.urls import re_path

from app_keepcon.consumers import KeepconConsumer

websocket_urlpatterns = [
    re_path(r"^ws/keepcon/$", KeepconConsumer.as_asgi()),
]
