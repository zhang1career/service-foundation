from django.urls import path, re_path

from app_oss.views.s3_unified_view import S3UnifiedView
from app_oss.views.s3_bucket_view import S3ListBucketsView

urlpatterns = [
    # GET / - List buckets
    path('', S3ListBucketsView.as_view(), name='s3-list-buckets'),
    # Object operations: /{bucket}/{key}
    re_path(r'^(?P<bucket>[^/]+)/(?P<key>.+)$', S3UnifiedView.as_view(), name='s3-object'),
    # Bucket operations: /{bucket} - list objects, POST ?delete
    path("<str:bucket>", S3UnifiedView.as_view(), name='s3-bucket'),
]
