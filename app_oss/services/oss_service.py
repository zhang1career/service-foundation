import logging
from django.http import HttpResponse
from urllib.parse import unquote

from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.services.oss_client import OSSClient

logger = logging.getLogger(__name__)


def handle_copy(request, bucket: str, key: str, copy_source: str):
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

        client = OSSClient()
        if not source_bucket:
            source_bucket = client.get_default_bucket()
        if not bucket:
            bucket = client.get_default_bucket()

        # Perform copy operation
        local_storage = client.get_local_storage()
        # Get source object
        source_obj = local_storage.get_object(
            bucket_name=source_bucket,
            object_key=source_key
        )
        # Determine metadata to use
        final_metadata = None
        if metadata_directive == "REPLACE" and metadata:
            final_metadata = metadata
        elif metadata_directive == "COPY" and source_obj.get('Metadata'):
            final_metadata = source_obj.get('Metadata')
            if metadata:
                # Merge new metadata with existing
                final_metadata.update(metadata)
        elif metadata:
            final_metadata = metadata
        # Put destination object
        local_storage.put_object(
            bucket_name=bucket,
            object_key=key,
            data=source_obj['Body'],
            content_type=source_obj.get('ContentType'),
            metadata=final_metadata
        )

        # Get destination object metadata to retrieve ETag and LastModified
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
        logger.error(f"[s3put] Source object not found: {e}")
        return HttpResponse("Source object not found", status=404)
    except Exception as e:
        logger.exception(f"[s3put] Error copying {copy_source} to {bucket}/{key}: {e}")
        return HttpResponse(str(e), status=500)


def handle_upload(request, bucket: str, key: str):
    """
    Handle regular upload operation

    Args:
        request: HTTP request
        bucket: Bucket name
        key: Object key (path)
    """
    try:
        # URL decode bucket and key in case they're encoded
        bucket = unquote(bucket) if bucket else bucket
        key = unquote(key) if key else key
        
        # Validate parameters
        if not bucket:
            return HttpResponse("Bucket name is required", status=400)
        if not key:
            return HttpResponse("Object key is required", status=400)
        
        client = OSSClient()

        # Read request body
        data = request.body

        # Get content type from headers
        content_type = request.META.get('CONTENT_TYPE', 'application/octet-stream')
        # Remove charset if present (e.g., "text/plain; charset=utf-8" -> "text/plain")
        if ';' in content_type:
            content_type = content_type.split(';')[0].strip()

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
    
    except Exception as e:
        logger.exception(f"[handle_upload] Error uploading {bucket}/{key}: {e}")
        return HttpResponse(str(e), status=500)
