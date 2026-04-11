from django.urls import path, re_path

from app_cms.views.cms_health_view import CmsHealthView
from app_cms.views.content_api_view import CmsContentDetailApiView, CmsContentListApiView

CONTENT_ROUTE = r"(?P<content_route>[a-z0-9][a-z0-9_-]*)"
RECORD_ID_RE = r"(?P<record_id>[0-9]+)"

urlpatterns = [
    path("health", CmsHealthView.as_view(), name="cms-health"),
    re_path(
        rf"^{CONTENT_ROUTE}/{RECORD_ID_RE}/$",
        CmsContentDetailApiView.as_view(),
        name="cms-content-detail",
    ),
    re_path(
        rf"^{CONTENT_ROUTE}/$",
        CmsContentListApiView.as_view(),
        name="cms-content-list",
    ),
]
