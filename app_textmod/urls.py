from django.urls import path

from app_textmod.views.health_view import TextmodHealthView
from app_textmod.views.scan_view import TextmodScanView

urlpatterns = [
    path("health", TextmodHealthView.as_view(), name="textmod-health"),
    path("scan", TextmodScanView.as_view(), name="textmod-scan"),
]
