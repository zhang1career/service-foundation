"""
S3-compatible REST API views

This module provides AWS S3-compatible REST API endpoints:
- PUT /{bucket}/{key} - Upload object
- PUT /{bucket}/{key} with x-amz-copy-source - Copy object (S3 CopyObject)
- GET /{bucket}/{key} - Download object
- DELETE /{bucket}/{key} - Delete object
- HEAD /{bucket}/{key} - Get object metadata
- GET /{bucket}?list-type=1|2&prefix=... - List objects (V1 or V2)
"""
import logging
import re
from django.http import HttpResponse
from rest_framework.views import APIView

from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.services.oss_client import OSSClient
from app_oss.services.oss_service import handle_copy, handle_upload
from app_oss.utils.s3_error_response import s3_error_response

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
            return s3_error_response('InternalError', str(e), resource=f'/{bucket}/{key}')


class S3GetObjectView(APIView):
    """S3-compatible GET object endpoint: GET /{bucket}/{key}"""

    def get(self, request, bucket: str, key: str):
        """
        Download an object (S3 GET operation). Supports Range header for partial content.
        """
        resource = f'/{bucket}/{key}'
        try:
            client = OSSClient()
            local_storage = client.get_local_storage()
            result = local_storage.get_object(bucket_name=bucket, object_key=key)

            # Handle Range request
            range_header = request.META.get('HTTP_RANGE')
            if range_header:
                return _build_range_response(result, range_header, resource)
            return _build_response(result)
        except (FileNotFoundError, ObjectNotFoundException):
            return s3_error_response('NoSuchKey', resource=resource)
        except Exception as e:
            logger.exception(f"[S3GetObjectView] Error downloading {bucket}/{key}: {e}")
            return s3_error_response('InternalError', str(e), resource=resource)


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
            return s3_error_response('InternalError', str(e), resource=f'/{bucket}/{key}')


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
        except (FileNotFoundError, ObjectNotFoundException):
            return s3_error_response('NoSuchKey', resource=f'/{bucket}/{key}')
        except Exception as e:
            logger.exception(f"[S3HeadObjectView] Error getting metadata for {bucket}/{key}: {e}")
            return s3_error_response('InternalError', str(e), resource=f'/{bucket}/{key}')


def _parse_range_header(range_header: str, total_size: int) -> tuple:
    """Parse Range: bytes=start-end. Returns (start, end) or None if invalid."""
    m = re.match(r'bytes=(\d*)-(\d*)', range_header.strip())
    if not m:
        return None
    start_s, end_s = m.group(1), m.group(2)
    if not start_s and not end_s:
        return None
    start = int(start_s) if start_s else 0
    end = (int(end_s) if end_s else total_size - 1)
    if start > end or start >= total_size:
        return None
    end = min(end, total_size - 1)
    return (start, end)


def _build_range_response(result, range_header: str, resource: str):
    """Build 206 Partial Content response."""
    body = result.get('Body', b'')
    total = len(body)
    parsed = _parse_range_header(range_header, total)
    if parsed is None:
        return s3_error_response(
            'InvalidRange',
            f'Cannot satisfy range request. Object size: {total}.',
            resource=resource,
        )
    start, end = parsed
    chunk = body[start:end + 1]
    response = HttpResponse(chunk, status=206)
    response['Content-Type'] = result.get('ContentType', 'application/octet-stream')
    response['Content-Length'] = str(len(chunk))
    response['Content-Range'] = f'bytes {start}-{end}/{total}'
    response['Last-Modified'] = result['LastModified'].strftime('%a, %d %b %Y %H:%M:%S GMT')
    response['ETag'] = f'"{result["ETag"]}"'
    if result.get('Metadata'):
        for meta_key, meta_value in result['Metadata'].items():
            response[f'x-amz-meta-{meta_key}'] = meta_value
    return response


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


class S3ListObjectsView(APIView):
    """S3-compatible ListObjects endpoint: GET /{bucket}?list-type=1|2&prefix=...&delimiter=..."""

    def get(self, request, bucket: str):
        resource = f'/{bucket}'
        try:
            client = OSSClient()
            local_storage = client.get_local_storage()

            list_type = request.GET.get('list-type', '2')
            prefix = request.GET.get('prefix', '')
            delimiter = request.GET.get('delimiter', '')
            max_keys = min(int(request.GET.get('max-keys', '1000')), 1000)

            if list_type == '1':
                marker = request.GET.get('marker', '')
                result = local_storage.list_objects_v1(
                    bucket_name=bucket,
                    prefix=prefix or None,
                    delimiter=delimiter or None,
                    max_keys=max_keys,
                    marker=marker or None,
                )
                return _build_list_objects_v1_xml(bucket, prefix, delimiter, max_keys, result)
            else:
                continuation_token = request.GET.get('continuation-token')
                start_after = request.GET.get('start-after')
                result = local_storage.list_objects_v2(
                    bucket_name=bucket,
                    prefix=prefix or None,
                    delimiter=delimiter or None,
                    max_keys=max_keys,
                    continuation_token=continuation_token,
                    start_after=start_after or None,
                )
                return _build_list_objects_v2_xml(bucket, prefix, delimiter, max_keys, result)
        except Exception as e:
            logger.exception(f"[S3ListObjectsView] Error listing objects in {bucket}: {e}")
            return s3_error_response('InternalError', str(e), resource=resource)


def _xml_escape(s: str) -> str:
    from xml.sax.saxutils import escape
    return escape(str(s))


def _obj_xml(obj, last_modified_key='LastModified'):
    lm = obj.get(last_modified_key) or obj.get('LastModified')
    lm_str = lm.strftime('%Y-%m-%dT%H:%M:%S.000Z') if hasattr(lm, 'strftime') else str(lm)
    etag = obj.get('ETag', '')
    if etag and not etag.startswith('"'):
        etag = f'"{etag}"'
    return (
        f'<Key>{_xml_escape(obj["Key"])}</Key>'
        f'<LastModified>{lm_str}</LastModified>'
        f'<ETag>{_xml_escape(etag)}</ETag>'
        f'<Size>{obj["Size"]}</Size>'
        '<StorageClass>STANDARD</StorageClass>'
    )


def _build_list_objects_v2_xml(bucket, prefix, delimiter, max_keys, result):
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
        f'<Name>{_xml_escape(bucket)}</Name>',
        f'<Prefix>{_xml_escape(prefix)}</Prefix>',
        f'<KeyCount>{result.get("KeyCount", 0)}</KeyCount>',
        f'<MaxKeys>{max_keys}</MaxKeys>',
        f'<IsTruncated>{"true" if result.get("IsTruncated", False) else "false"}</IsTruncated>',
    ]
    if result.get('NextContinuationToken'):
        xml_parts.append(f'<NextContinuationToken>{_xml_escape(result["NextContinuationToken"])}</NextContinuationToken>')
    if delimiter:
        xml_parts.append(f'<Delimiter>{_xml_escape(delimiter)}</Delimiter>')
    for obj in result.get('Contents', []):
        xml_parts.append(f'<Contents>{_obj_xml(obj)}</Contents>')
    for cp in result.get('CommonPrefixes', []):
        xml_parts.append(f'<CommonPrefixes><Prefix>{_xml_escape(cp["Prefix"])}</Prefix></CommonPrefixes>')
    xml_parts.append('</ListBucketResult>')
    return HttpResponse('\n'.join(xml_parts), content_type='application/xml')


def _build_list_objects_v1_xml(bucket, prefix, delimiter, max_keys, result):
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
        f'<Name>{_xml_escape(bucket)}</Name>',
        f'<Prefix>{_xml_escape(prefix)}</Prefix>',
        f'<Marker>{_xml_escape(result.get("Marker", ""))}</Marker>',
        f'<MaxKeys>{max_keys}</MaxKeys>',
        f'<IsTruncated>{"true" if result.get("IsTruncated", False) else "false"}</IsTruncated>',
    ]
    if result.get('NextMarker'):
        xml_parts.append(f'<NextMarker>{_xml_escape(result["NextMarker"])}</NextMarker>')
    if delimiter:
        xml_parts.append(f'<Delimiter>{_xml_escape(delimiter)}</Delimiter>')
    for obj in result.get('Contents', []):
        xml_parts.append(f'<Contents>{_obj_xml(obj)}</Contents>')
    for cp in result.get('CommonPrefixes', []):
        xml_parts.append(f'<CommonPrefixes><Prefix>{_xml_escape(cp["Prefix"])}</Prefix></CommonPrefixes>')
    xml_parts.append('</ListBucketResult>')
    return HttpResponse('\n'.join(xml_parts), content_type='application/xml')
