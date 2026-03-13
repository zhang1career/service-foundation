"""
Unified S3-compatible REST API view

This view handles all S3 operations based on HTTP method and URL pattern:
- GET / - List buckets
- GET /{bucket}?list-type=1|2 - List objects
- POST /{bucket}?delete - Delete multiple objects
- PUT/GET/DELETE/HEAD /{bucket}/{key} - Object operations
"""
import logging
from django.http import HttpResponse
from rest_framework.views import APIView

from app_oss.utils.s3_error_response import s3_error_response
from app_oss.views.s3_compatible_view import (
    S3PutObjectView,
    S3GetObjectView,
    S3DeleteObjectView,
    S3HeadObjectView,
    S3ListObjectsView,
)
from app_oss.views.s3_bucket_view import S3ListBucketsView, S3DeleteMultipleObjectsView

logger = logging.getLogger(__name__)


class S3UnifiedView(APIView):
    """Unified S3-compatible view that routes based on HTTP method and URL pattern"""

    def dispatch(self, request, *args, **kwargs):
        bucket = kwargs.get('bucket')

        # Bucket-level: GET list, POST ?delete
        if 'key' not in kwargs or not kwargs.get('key'):
            if request.method == 'GET':
                view = S3ListObjectsView.as_view()
                return view(request, bucket=bucket)
            elif request.method == 'POST' and request.GET.get('delete'):
                view = S3DeleteMultipleObjectsView.as_view()
                return view(request, bucket=bucket)
            return s3_error_response('MethodNotAllowed', resource=f'/{bucket or ""}')
        
        # This is an object operation
        method = request.method.upper()
        
        if method == 'PUT':
            view = S3PutObjectView.as_view()
        elif method == 'GET':
            view = S3GetObjectView.as_view()
        elif method == 'DELETE':
            view = S3DeleteObjectView.as_view()
        elif method == 'HEAD':
            view = S3HeadObjectView.as_view()
        else:
            return HttpResponse("Method not allowed", status=405)
        
        return view(request, bucket=kwargs.get('bucket'), key=kwargs.get('key'))
