"""
S3-compatible REST API views

This module provides AWS S3-compatible REST API endpoints:
- PUT /{bucket}/{key} - Upload object
- PUT /{bucket}/{key} with x-amz-copy-source - Copy object (S3 CopyObject)
- GET /{bucket}/{key} - Download object
- DELETE /{bucket}/{key} - Delete object
- HEAD /{bucket}/{key} - Get object metadata
- GET /{bucket}?list-type=2&prefix=... - List objects
"""
import logging
from django.http import HttpResponse
from rest_framework.views import APIView

from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.services.oss_client import OSSClient
from app_oss.services.oss_service import handle_copy, handle_upload

logger = logging.getLogger(__name__)


class S3PutObjectView(APIView):
    """S3-compatible PUT object endpoint: PUT /{bucket}/{key}"""

    def put(self, request, bucket: str, key: str):
        """
        Upload an object or copy an object (S3 PUT operation)
        
        Supports:
        - Regular upload: PUT /{bucket}/{key} with body
        - Copy operation: PUT /{bucket}/{key} with x-amz-copy-source header (S3 CopyObject)
        
        Args:
            request: HTTP request
            bucket: Bucket name
            key: Object key (path)
        """
        try:
            # Check if this is a copy operation
            copy_source = request.META.get('HTTP_X_AMZ_COPY_SOURCE')
            if copy_source:
                return handle_copy(request, bucket, key, copy_source)
            else:
                return handle_upload(request, bucket, key)

        except Exception as e:
            logger.exception(f"[s3put] Error processing {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)


class S3GetObjectView(APIView):
    """S3-compatible GET object endpoint: GET /{bucket}/{key}"""

    def get(self, request, bucket: str, key: str):
        """
        Download an object (S3 GET operation)
        
        Args:
            request: HTTP request
            bucket: Bucket name
            key: Object key (path)
        """
        try:
            client = OSSClient()

            local_storage = client.get_local_storage()
            result = local_storage.get_object(
                bucket_name=bucket,
                object_key=key
            )
            # Return S3-compatible response
            return _build_response(result)
        except FileNotFoundError:
            return HttpResponse("Not Found", status=404)
        except ObjectNotFoundException:
            return HttpResponse("Not Found", status=404)
        except Exception as e:
            logger.exception(f"[S3GetObjectView] Error downloading {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)


class S3DeleteObjectView(APIView):
    """S3-compatible DELETE object endpoint: DELETE /{bucket}/{key}"""

    def delete(self, request, bucket: str, key: str):
        """
        Delete an object (S3 DELETE operation)
        
        Args:
            request: HTTP request
            bucket: Bucket name
            key: Object key (path)
        """
        try:
            client = OSSClient()

            local_storage = client.get_local_storage()
            local_storage.delete_object(
                bucket_name=bucket,
                object_key=key
            )

            # Return S3-compatible response (204 No Content)
            return HttpResponse(status=204)

        except Exception as e:
            logger.exception(f"[S3DeleteObjectView] Error deleting {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)


class S3HeadObjectView(APIView):
    """S3-compatible HEAD object endpoint: HEAD /{bucket}/{key}"""

    def head(self, request, bucket: str, key: str):
        """
        Get object metadata (S3 HEAD operation)
        
        Args:
            request: HTTP request
            bucket: Bucket name
            key: Object key (path)
        """
        try:
            client = OSSClient()

            local_storage = client.get_local_storage()
            result = local_storage.head_object(
                bucket_name=bucket,
                object_key=key
            )
            # Return S3-compatible response
            return _build_response(result)
        except FileNotFoundError:
            return HttpResponse("Not Found", status=404)
        except ObjectNotFoundException:
            return HttpResponse("Not Found", status=404)
        except Exception as e:
            logger.exception(f"[S3HeadObjectView] Error getting metadata for {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)


def _build_response(result):
    # For HEAD requests, Body might not be present
    body = result.get('Body', b'')
    response = HttpResponse(body, status=200)
    response['Content-Type'] = result.get('ContentType', 'application/octet-stream')
    response['Content-Length'] = str(result['ContentLength'])
    response['Last-Modified'] = result['LastModified'].strftime('%a, %d %b %Y %H:%M:%S GMT')
    response['ETag'] = f'"{result["ETag"]}"'
    # Add metadata headers
    if result.get('Metadata'):
        for meta_key, meta_value in result['Metadata'].items():
            response[f'x-amz-meta-{meta_key}'] = meta_value
    return response


class S3ListObjectsV2View(APIView):
    """S3-compatible ListObjectsV2 endpoint: GET /{bucket}?list-type=2&prefix=..."""

    def get(self, request, bucket: str):
        """
        List objects in a bucket (S3 ListObjectsV2 operation)
        
        Args:
            request: HTTP request
            bucket: Bucket name
        """
        try:
            client = OSSClient()

            # Get query parameters
            list_type = request.GET.get('list-type', '2')
            if list_type != '2':
                return HttpResponse("Only list-type=2 is supported", status=400)
            prefix = request.GET.get('prefix', '')
            max_keys = int(request.GET.get('max-keys', '1000'))
            continuation_token = request.GET.get('continuation-token')

            local_storage = client.get_local_storage()
            result = local_storage.list_objects_v2(
                bucket_name=bucket,
                prefix=prefix if prefix else None,
                max_keys=max_keys,
                continuation_token=continuation_token
            )
            return _build_xml_response(bucket, prefix, max_keys, result)
        except Exception as e:
            logger.exception(f"[S3ListObjectsV2View] Error listing objects in {bucket}: {e}")
            return HttpResponse(str(e), status=500)


def _build_xml_response(bucket, prefix, max_keys, result):
    # Format response as XML (S3-compatible format)
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">', f'<Name>{bucket}</Name>',
        f'<Prefix>{prefix}</Prefix>', f'<KeyCount>{result.get("KeyCount", 0)}</KeyCount>',
        f'<MaxKeys>{max_keys}</MaxKeys>',
        f'<IsTruncated>{"true" if result.get("IsTruncated", False) else "false"}</IsTruncated>'
    ]
    if result.get('NextContinuationToken'):
        xml_parts.append(f'<NextContinuationToken>{result["NextContinuationToken"]}</NextContinuationToken>')
    # Add objects
    for obj in result.get('Contents', []):
        xml_parts.append('<Contents>')
        xml_parts.append(f'<Key>{obj["Key"]}</Key>')
        xml_parts.append(
            f'<LastModified>{obj["LastModified"].strftime("%Y-%m-%dT%H:%M:%S.000Z") if hasattr(obj["LastModified"], "strftime") else obj["LastModified"]}</LastModified>')
        # Format ETag: ensure it's wrapped in quotes
        etag = obj["ETag"]
        if not etag.startswith('"'):
            etag = f'"{etag}"'
        xml_parts.append(f'<ETag>{etag}</ETag>')
        xml_parts.append(f'<Size>{obj["Size"]}</Size>')
        xml_parts.append('<StorageClass>STANDARD</StorageClass>')
        xml_parts.append('</Contents>')
    xml_parts.append('</ListBucketResult>')
    xml_response = '\n'.join(xml_parts)

    return HttpResponse(xml_response, content_type='application/xml')
