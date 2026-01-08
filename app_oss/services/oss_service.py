import logging
from typing import Optional, List, Dict, Any

from app_oss.consts.oss_const import (
    DEFAULT_PRESIGNED_URL_EXPIRES_IN,
    MAX_PRESIGNED_URL_EXPIRES_IN,
    DEFAULT_MAX_KEYS,
    MAX_KEYS_LIMIT,
    DEFAULT_CONTENT_TYPE,
    CLIENT_METHOD_GET,
    CLIENT_METHOD_PUT,
    CLIENT_METHOD_DELETE,
)
from app_oss.exceptions.upload_exception import UploadException
from app_oss.exceptions.download_exception import DownloadException
from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.services.oss_client import OSSClient

logger = logging.getLogger(__name__)


def _get_bucket_name(bucket_name: Optional[str] = None) -> str:
    """
    Get bucket name, use default if not provided
    
    Args:
        bucket_name: Optional bucket name
        
    Returns:
        Bucket name to use
        
    Raises:
        ConfigurationErrorException: If no bucket name is configured
    """
    if bucket_name:
        return bucket_name
    
    default_bucket = OSSClient().get_default_bucket()
    if not default_bucket:
        from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
        raise ConfigurationErrorException("No bucket name provided and no default bucket configured")
    
    return default_bucket


def upload_file(
    file_path: str,
    object_key: str,
    bucket_name: Optional[str] = None,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a file to OSS
    
    Args:
        file_path: Path to the file to upload
        object_key: Object key (path) in the bucket
        bucket_name: Optional bucket name (uses default if not provided)
        content_type: Optional content type
        metadata: Optional metadata dictionary
        
    Returns:
        Dictionary with upload result information
        
    Raises:
        UploadException: If upload fails
    """
    logger.info("[oss_upload_file] file_path=%s, object_key=%s, bucket=%s",
                file_path, object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        with open(file_path, 'rb') as f:
            data = f.read()
        result = local_storage.put_object(
            bucket_name=bucket,
            object_key=object_key,
            data=data,
            content_type=content_type,
            metadata=metadata
        )
        
        logger.info("[oss_upload_file] Upload successful: object_key=%s", object_key)
        return {
            "object_key": object_key,
            "bucket": bucket,
            "success": True
        }
    except FileNotFoundError as e:
        logger.error("[oss_upload_file] File not found: %s", file_path)
        raise UploadException(f"File not found: {file_path}") from e
    except Exception as e:
        logger.exception("[oss_upload_file] Unexpected error: %s", str(e))
        raise UploadException(f"Upload failed: {str(e)}") from e


def upload_fileobj(
    file_obj,
    object_key: str,
    bucket_name: Optional[str] = None,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a file object to OSS
    
    Args:
        file_obj: File-like object to upload
        object_key: Object key (path) in the bucket
        bucket_name: Optional bucket name (uses default if not provided)
        content_type: Optional content type
        metadata: Optional metadata dictionary
        
    Returns:
        Dictionary with upload result information
        
    Raises:
        UploadException: If upload fails
    """
    logger.info("[oss_upload_fileobj] object_key=%s, bucket=%s", object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        data = file_obj.read()
        result = local_storage.put_object(
            bucket_name=bucket,
            object_key=object_key,
            data=data,
            content_type=content_type or DEFAULT_CONTENT_TYPE,
            metadata=metadata
        )
        
        logger.info("[oss_upload_fileobj] Upload successful: object_key=%s", object_key)
        return {
            "object_key": object_key,
            "bucket": bucket,
            "success": True
        }
    except Exception as e:
        logger.exception("[oss_upload_fileobj] Unexpected error: %s", str(e))
        raise UploadException(f"Upload failed: {str(e)}") from e


def download_file(
    object_key: str,
    file_path: str,
    bucket_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download a file from OSS to local path
    
    Args:
        object_key: Object key (path) in the bucket
        file_path: Local path to save the file
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Dictionary with download result information
        
    Raises:
        DownloadException: If download fails
        ObjectNotFoundException: If object does not exist
    """
    logger.info("[oss_download_file] object_key=%s, file_path=%s, bucket=%s",
                object_key, file_path, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        result = local_storage.get_object(bucket_name=bucket, object_key=object_key)
        with open(file_path, 'wb') as f:
            f.write(result['Body'])
        
        logger.info("[oss_download_file] Download successful: object_key=%s", object_key)
        return {
            "object_key": object_key,
            "file_path": file_path,
            "bucket": bucket,
            "success": True
        }
    except FileNotFoundError as e:
        logger.error("[oss_download_file] Object not found: object_key=%s", object_key)
        raise ObjectNotFoundException(f"Object not found: {object_key}") from e
    except Exception as e:
        logger.exception("[oss_download_file] Unexpected error: %s", str(e))
        raise DownloadException(f"Download failed: {str(e)}") from e


def download_fileobj(
    object_key: str,
    file_obj,
    bucket_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download a file from OSS to file object
    
    Args:
        object_key: Object key (path) in the bucket
        file_obj: File-like object to write to
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Dictionary with download result information
        
    Raises:
        DownloadException: If download fails
        ObjectNotFoundException: If object does not exist
    """
    logger.info("[oss_download_fileobj] object_key=%s, bucket=%s", object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        result = local_storage.get_object(bucket_name=bucket, object_key=object_key)
        file_obj.write(result['Body'])
        
        logger.info("[oss_download_fileobj] Download successful: object_key=%s", object_key)
        return {
            "object_key": object_key,
            "bucket": bucket,
            "success": True
        }
    except FileNotFoundError as e:
        logger.error("[oss_download_fileobj] Object not found: object_key=%s", object_key)
        raise ObjectNotFoundException(f"Object not found: {object_key}") from e
    except Exception as e:
        logger.exception("[oss_download_fileobj] Unexpected error: %s", str(e))
        raise DownloadException(f"Download failed: {str(e)}") from e


def list_objects(
    prefix: Optional[str] = None,
    bucket_name: Optional[str] = None,
    max_keys: int = DEFAULT_MAX_KEYS
) -> Dict[str, Any]:
    """
    List objects in a bucket
    
    Args:
        prefix: Optional prefix to filter objects
        bucket_name: Optional bucket name (uses default if not provided)
        max_keys: Maximum number of keys to return (default: 1000, max: 10000)
        
    Returns:
        Dictionary with list of objects and metadata
        
    Raises:
        ConfigurationErrorException: If max_keys exceeds limit
    """
    logger.info("[oss_list_objects] prefix=%s, bucket=%s, max_keys=%d", prefix, bucket_name, max_keys)
    
    if max_keys > MAX_KEYS_LIMIT:
        from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
        raise ConfigurationErrorException(f"max_keys cannot exceed {MAX_KEYS_LIMIT}")
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        response = local_storage.list_objects_v2(
            bucket_name=bucket,
            prefix=prefix,
            max_keys=max_keys
        )
        
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                last_modified = obj.get('LastModified')
                if hasattr(last_modified, 'isoformat'):
                    last_modified = last_modified.isoformat()
                elif isinstance(last_modified, str):
                    pass  # Already a string
                else:
                    last_modified = None
                
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': last_modified,
                    'etag': obj.get('ETag', '').strip('"'),
                })
        
        result = {
            "bucket": bucket,
            "prefix": prefix,
            "is_truncated": response.get('IsTruncated', False),
            "key_count": len(objects),
            "objects": objects
        }
        
        if response.get('IsTruncated'):
            result['next_continuation_token'] = response.get('NextContinuationToken')
        
        logger.info("[oss_list_objects] Found %d objects", len(objects))
        return result
    except Exception as e:
        logger.exception("[oss_list_objects] Unexpected error: %s", str(e))
        raise Exception(f"List objects failed: {str(e)}") from e


def delete_object(
    object_key: str,
    bucket_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete an object from OSS
    
    Args:
        object_key: Object key (path) in the bucket
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Dictionary with delete result information
        
    Raises:
        ObjectNotFoundException: If object does not exist
    """
    logger.info("[oss_delete_object] object_key=%s, bucket=%s", object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        if not local_storage.object_exists(bucket_name=bucket, object_key=object_key):
            raise ObjectNotFoundException(f"Object not found: {object_key}")
        local_storage.delete_object(bucket_name=bucket, object_key=object_key)
        
        logger.info("[oss_delete_object] Delete successful: object_key=%s", object_key)
        return {
            "object_key": object_key,
            "bucket": bucket,
            "success": True
        }
    except FileNotFoundError as e:
        logger.error("[oss_delete_object] Object not found: object_key=%s", object_key)
        raise ObjectNotFoundException(f"Object not found: {object_key}") from e
    except Exception as e:
        logger.exception("[oss_delete_object] Unexpected error: %s", str(e))
        raise Exception(f"Delete failed: {str(e)}") from e


def object_exists(
    object_key: str,
    bucket_name: Optional[str] = None
) -> bool:
    """
    Check if an object exists in OSS
    
    Args:
        object_key: Object key (path) in the bucket
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        True if object exists, False otherwise
    """
    logger.info("[oss_object_exists] object_key=%s, bucket=%s", object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        exists = local_storage.object_exists(bucket_name=bucket, object_key=object_key)
        logger.info("[oss_object_exists] Object exists: %s, object_key=%s", exists, object_key)
        return exists
    except FileNotFoundError:
        logger.info("[oss_object_exists] Object does not exist: object_key=%s", object_key)
        return False
    except Exception as e:
        logger.exception("[oss_object_exists] Unexpected error: %s", str(e))
        raise Exception(f"Error checking object existence: {str(e)}") from e


def generate_presigned_url(
    object_key: str,
    method: str = CLIENT_METHOD_GET,
    expires_in: int = DEFAULT_PRESIGNED_URL_EXPIRES_IN,
    bucket_name: Optional[str] = None
) -> str:
    """
    Generate a presigned URL for an object
    
    Args:
        object_key: Object key (path) in the bucket
        method: Client method ('get_object', 'put_object', 'delete_object')
        expires_in: Expiration time in seconds (default: 3600, max: 604800)
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Presigned URL string
        
    Raises:
        ConfigurationErrorException: If expires_in exceeds limit or using local storage
    """
    logger.info("[oss_generate_presigned_url] object_key=%s, method=%s, expires_in=%d, bucket=%s",
                object_key, method, expires_in, bucket_name)
    
    if expires_in > MAX_PRESIGNED_URL_EXPIRES_IN:
        from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
        raise ConfigurationErrorException(
            f"expires_in cannot exceed {MAX_PRESIGNED_URL_EXPIRES_IN} seconds"
        )
    
    try:
        # For local storage, presigned URLs are not applicable
        # Return a direct access URL instead (if service is accessible)
        # Note: This is a simplified implementation
        from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
        raise ConfigurationErrorException(
            "Presigned URLs are not supported in local storage mode. Use direct API access instead."
        )
    except Exception as e:
        logger.exception("[oss_generate_presigned_url] Unexpected error: %s", str(e))
        raise Exception(f"Failed to generate presigned URL: {str(e)}") from e


def get_object_metadata(
    object_key: str,
    bucket_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get object metadata
    
    Args:
        object_key: Object key (path) in the bucket
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Dictionary with object metadata
        
    Raises:
        ObjectNotFoundException: If object does not exist
    """
    logger.info("[oss_get_object_metadata] object_key=%s, bucket=%s", object_key, bucket_name)
    
    try:
        client = OSSClient()
        bucket = _get_bucket_name(bucket_name)
        
        local_storage = client.get_local_storage()
        response = local_storage.head_object(bucket_name=bucket, object_key=object_key)
        
        last_modified = response.get('LastModified')
        if hasattr(last_modified, 'isoformat'):
            last_modified = last_modified.isoformat()
        elif isinstance(last_modified, str):
            pass  # Already a string
        else:
            last_modified = None
        
        metadata = {
            "object_key": object_key,
            "bucket": bucket,
            "content_length": response.get('ContentLength'),
            "content_type": response.get('ContentType'),
            "last_modified": last_modified,
            "etag": response.get('ETag', '').strip('"'),
            "metadata": response.get('Metadata', {}),
        }
        
        logger.info("[oss_get_object_metadata] Metadata retrieved: object_key=%s", object_key)
        return metadata
    except FileNotFoundError as e:
        logger.error("[oss_get_object_metadata] Object not found: object_key=%s", object_key)
        raise ObjectNotFoundException(f"Object not found: {object_key}") from e
    except Exception as e:
        logger.exception("[oss_get_object_metadata] Unexpected error: %s", str(e))
        raise Exception(f"Failed to get object metadata: {str(e)}") from e


def copy_object(
    source_object_key: str,
    destination_object_key: str,
    source_bucket_name: Optional[str] = None,
    destination_bucket_name: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    metadata_directive: str = "COPY"
) -> Dict[str, Any]:
    """
    Copy an object within the same bucket or between buckets
    
    Args:
        source_object_key: Source object key (path) in the bucket
        destination_object_key: Destination object key (path) in the bucket
        source_bucket_name: Optional source bucket name (uses default if not provided)
        destination_bucket_name: Optional destination bucket name (uses source bucket if not provided)
        metadata: Optional metadata dictionary to set on the copied object
        metadata_directive: Either "COPY" (preserve source metadata) or "REPLACE" (use new metadata)
        
    Returns:
        Dictionary with copy result information
        
    Raises:
        ObjectNotFoundException: If source object does not exist
        UploadException: If copy fails
    """
    logger.info("[oss_copy_object] source_object_key=%s, destination_object_key=%s, "
                "source_bucket=%s, destination_bucket=%s",
                source_object_key, destination_object_key, source_bucket_name, destination_bucket_name)
    
    try:
        client = OSSClient()
        source_bucket = _get_bucket_name(source_bucket_name)
        destination_bucket = _get_bucket_name(destination_bucket_name) if destination_bucket_name else source_bucket
        
        local_storage = client.get_local_storage()
        
        # Get source object
        source_obj = local_storage.get_object(
            bucket_name=source_bucket,
            object_key=source_object_key
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
            bucket_name=destination_bucket,
            object_key=destination_object_key,
            data=source_obj['Body'],
            content_type=source_obj.get('ContentType'),
            metadata=final_metadata
        )
        
        logger.info("[oss_copy_object] Copy successful: source=%s, destination=%s",
                   source_object_key, destination_object_key)
        return {
            "source_object_key": source_object_key,
            "destination_object_key": destination_object_key,
            "source_bucket": source_bucket,
            "destination_bucket": destination_bucket,
            "success": True
        }
    except FileNotFoundError as e:
        logger.error("[oss_copy_object] Source object not found: source_object_key=%s", source_object_key)
        raise ObjectNotFoundException(f"Source object not found: {source_object_key}") from e
    except Exception as e:
        logger.exception("[oss_copy_object] Unexpected error: %s", str(e))
        raise UploadException(f"Copy failed: {str(e)}") from e

