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
from typing import Optional
from urllib.parse import unquote

from django.http import HttpResponse, Http404
from rest_framework.views import APIView

from app_oss.services.oss_client import OSSClient
from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.services.oss_service import copy_object

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
            bucket: Bucket name
            key: Object key (path)
        """
        try:
            # Check if this is a copy operation
            copy_source = request.META.get('HTTP_X_AMZ_COPY_SOURCE')
            if copy_source:
                return self._handle_copy(request, bucket, key, copy_source)
            else:
                return self._handle_upload(request, bucket, key)
                
        except Exception as e:
            logger.exception(f"[S3PutObjectView] Error processing {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)
    
    def _handle_copy(self, request, bucket: str, key: str, copy_source: str):
        """
        Handle S3 copy operation (CopyObject API)
        
        Args:
            request: HTTP request
            bucket: Destination bucket name
            key: Destination object key
            copy_source: Source object path (format: /bucket/key or bucket/key)
        """
        try:
            # Parse copy source (format: /bucket/key or bucket/key)
            # URL decode the copy source in case it's encoded
            copy_source = unquote(copy_source).lstrip('/')
            if '/' not in copy_source:
                return HttpResponse("Invalid x-amz-copy-source format", status=400)
            
            source_parts = copy_source.split('/', 1)
            source_bucket = source_parts[0]
            source_key = source_parts[1] if len(source_parts) > 1 else ''
            
            if not source_key:
                return HttpResponse("Invalid x-amz-copy-source: missing key", status=400)
            
            # Get metadata directive (COPY or REPLACE)
            metadata_directive = request.META.get('HTTP_X_AMZ_METADATA_DIRECTIVE', 'COPY').upper()
            if metadata_directive not in ['COPY', 'REPLACE']:
                metadata_directive = 'COPY'
            
            # Get user metadata from headers (x-amz-meta-*)
            metadata = {}
            for header_name, header_value in request.META.items():
                if header_name.startswith('HTTP_X_AMZ_META_'):
                    meta_key = header_name[16:].lower().replace('_', '-')
                    metadata[meta_key] = header_value
            
            # Perform copy operation
            result = copy_object(
                source_object_key=source_key,
                destination_object_key=key,
                source_bucket_name=source_bucket,
                destination_bucket_name=bucket,
                metadata=metadata if metadata else None,
                metadata_directive=metadata_directive
            )
            
            # Get destination object metadata to retrieve ETag and LastModified
            client = OSSClient()
            local_storage = client.get_local_storage()
            dest_metadata = local_storage.head_object(
                bucket_name=bucket,
                object_key=key
            )
            
            # Format ETag (ensure it's wrapped in quotes)
            etag = dest_metadata.get('ETag', '').strip('"')
            if not etag.startswith('"'):
                etag = f'"{etag}"'
            
            # Format LastModified
            last_modified = dest_metadata.get('LastModified')
            if hasattr(last_modified, 'strftime'):
                last_modified_str = last_modified.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            else:
                from datetime import datetime
                last_modified_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Return S3-compatible XML response for copy operation
            xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<CopyObjectResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <ETag>{etag}</ETag>
    <LastModified>{last_modified_str}</LastModified>
</CopyObjectResult>'''
            
            response = HttpResponse(xml_response, content_type='application/xml', status=200)
            return response
            
        except ObjectNotFoundException as e:
            logger.error(f"[S3PutObjectView] Source object not found: {copy_source}")
            return HttpResponse("Source object not found", status=404)
        except Exception as e:
            logger.exception(f"[S3PutObjectView] Error copying {copy_source} to {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)
    
    def _handle_upload(self, request, bucket: str, key: str):
        """
        Handle regular upload operation
        
        Args:
            request: HTTP request
            bucket: Bucket name
            key: Object key (path)
        """
        client = OSSClient()
        
        # Read request body
        data = request.body
        
        # Get content type from headers
        content_type = request.META.get('CONTENT_TYPE', 'application/octet-stream')
        
        # Get user metadata from headers (x-amz-meta-*)
        metadata = {}
        for header_name, header_value in request.META.items():
            if header_name.startswith('HTTP_X_AMZ_META_'):
                meta_key = header_name[16:].lower().replace('_', '-')
                metadata[meta_key] = header_value
        
        local_storage = client.get_local_storage()
        result = local_storage.put_object(
            bucket_name=bucket,
            object_key=key,
            data=data,
            content_type=content_type,
            metadata=metadata if metadata else None
        )
        
        # Return S3-compatible response
        response = HttpResponse(status=200)
        if 'ETag' in result:
            response['ETag'] = f'"{result["ETag"]}"'
        return response


class S3GetObjectView(APIView):
    """S3-compatible GET object endpoint: GET /{bucket}/{key}"""
    
    def get(self, request, bucket: str, key: str):
        """
        Download an object (S3 GET operation)
        
        Args:
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
            response = HttpResponse(
                result['Body'],
                content_type=result.get('ContentType', 'application/octet-stream')
            )
            response['Content-Length'] = str(result['ContentLength'])
            response['Last-Modified'] = result['LastModified'].strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['ETag'] = f'"{result["ETag"]}"'
            
            # Add metadata headers
            if result.get('Metadata'):
                for meta_key, meta_value in result['Metadata'].items():
                    response[f'x-amz-meta-{meta_key}'] = meta_value
            
            return response
                
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
            response = HttpResponse(status=200)
            response['Content-Type'] = result.get('ContentType', 'application/octet-stream')
            response['Content-Length'] = str(result['ContentLength'])
            response['Last-Modified'] = result['LastModified'].strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['ETag'] = f'"{result["ETag"]}"'
            
            # Add metadata headers
            if result.get('Metadata'):
                for meta_key, meta_value in result['Metadata'].items():
                    response[f'x-amz-meta-{meta_key}'] = meta_value
            
            return response
                
        except FileNotFoundError:
            return HttpResponse("Not Found", status=404)
        except ObjectNotFoundException:
            return HttpResponse("Not Found", status=404)
        except Exception as e:
            logger.exception(f"[S3HeadObjectView] Error getting metadata for {bucket}/{key}: {e}")
            return HttpResponse(str(e), status=500)


class S3ListObjectsV2View(APIView):
    """S3-compatible ListObjectsV2 endpoint: GET /{bucket}?list-type=2&prefix=..."""
    
    def get(self, request, bucket: str):
        """
        List objects in a bucket (S3 ListObjectsV2 operation)
        
        Args:
            bucket: Bucket name
        """
        try:
            client = OSSClient()
            
            # Get query parameters
            list_type = request.GET.get('list-type', '2')
            prefix = request.GET.get('prefix', '')
            max_keys = int(request.GET.get('max-keys', '1000'))
            continuation_token = request.GET.get('continuation-token')
            
            if list_type != '2':
                return HttpResponse("Only list-type=2 is supported", status=400)
            
            local_storage = client.get_local_storage()
            result = local_storage.list_objects_v2(
                bucket_name=bucket,
                prefix=prefix if prefix else None,
                max_keys=max_keys,
                continuation_token=continuation_token
            )
            
            # Format response as XML (S3-compatible format)
            xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_parts.append('<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
            xml_parts.append(f'<Name>{bucket}</Name>')
            xml_parts.append(f'<Prefix>{prefix}</Prefix>')
            xml_parts.append(f'<KeyCount>{result.get("KeyCount", 0)}</KeyCount>')
            xml_parts.append(f'<MaxKeys>{max_keys}</MaxKeys>')
            xml_parts.append(f'<IsTruncated>{"true" if result.get("IsTruncated", False) else "false"}</IsTruncated>')
            
            if result.get('NextContinuationToken'):
                xml_parts.append(f'<NextContinuationToken>{result["NextContinuationToken"]}</NextContinuationToken>')
            
            # Add objects
            for obj in result.get('Contents', []):
                xml_parts.append('<Contents>')
                xml_parts.append(f'<Key>{obj["Key"]}</Key>')
                xml_parts.append(f'<LastModified>{obj["LastModified"].strftime("%Y-%m-%dT%H:%M:%S.000Z") if hasattr(obj["LastModified"], "strftime") else obj["LastModified"]}</LastModified>')
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
            
            response = HttpResponse(xml_response, content_type='application/xml')
            return response
                
        except Exception as e:
            logger.exception(f"[S3ListObjectsV2View] Error listing objects in {bucket}: {e}")
            return HttpResponse(str(e), status=500)

