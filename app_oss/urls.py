from django.urls import path, re_path

from common.views.dict_codes_view import DictCodesView
from app_oss.views.oss_health_view import OssHealthView
from app_oss.views.s3_unified_view import S3UnifiedView
from app_oss.views.s3_bucket_view import S3ListBucketsView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="oss-dict"),
    path("health", OssHealthView.as_view(), name="oss-health"),
    # GET / - List buckets
    path('', S3ListBucketsView.as_view(), name='s3-list-buckets'),
    # Object operations: /{bucket}/{key}
    re_path(r'^(?P<bucket>[^/]+)/(?P<key>.+)$', S3UnifiedView.as_view(), name='s3-object'),
    # Bucket operations: /{bucket} - list objects, POST ?delete
    path("<str:bucket>", S3UnifiedView.as_view(), name='s3-bucket'),
]
