"""
Unified S3-compatible REST API view

This view handles all S3 operations based on HTTP method:
- PUT /{bucket}/{key} - Upload object
- GET /{bucket}/{key} - Download object
- DELETE /{bucket}/{key} - Delete object
- HEAD /{bucket}/{key} - Get object metadata
- GET /{bucket}?list-type=2&prefix=... - List objects
"""
import logging
from django.http import HttpResponse
from rest_framework.views import APIView

from app_oss.views.s3_compatible_view import (
    S3PutObjectView,
    S3GetObjectView,
    S3DeleteObjectView,
    S3HeadObjectView,
    S3ListObjectsV2View,
)

logger = logging.getLogger(__name__)


class S3UnifiedView(APIView):
    """Unified S3-compatible view that routes based on HTTP method and URL pattern"""
    
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch request based on HTTP method and URL pattern
        
        If 'key' is in kwargs, route to object operations (PUT/GET/DELETE/HEAD)
        Otherwise, route to bucket operations (GET for list)
        """
        # Check if this is a list operation (bucket only, no key)
        if 'key' not in kwargs or not kwargs.get('key'):
            # This is a bucket list operation
            if request.method == 'GET':
                view = S3ListObjectsV2View.as_view()
                return view(request, bucket=kwargs.get('bucket'))
            else:
                return HttpResponse("Method not allowed", status=405)
        
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
