from django.urls import path, re_path

from app_oss.views.s3_unified_view import S3UnifiedView

urlpatterns = [
    # S3-compatible REST API endpoints
    # Pattern: /{bucket}/{key} for object operations (PUT/GET/DELETE/HEAD)
    # Pattern: /{bucket} for bucket operations (GET with list-type=2)
    # Note: The order matters - more specific patterns should come first
    re_path(r'^(?P<bucket>[^/]+)/(?P<key>.+)$', S3UnifiedView.as_view(), name='s3-object'),
    path("<str:bucket>", S3UnifiedView.as_view(), name='s3-bucket'),
]
