"""
Local file storage service for S3-compatible object storage

This module provides a local file system implementation that mimics
AWS S3 API behavior, allowing seamless switching between local storage
and AWS S3.
"""
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Local file storage service with S3-compatible API"""
    
    def __init__(self, storage_path: str):
        """
        Initialize local storage service
        
        Args:
            storage_path: Base path for storing objects
        """
        self.storage_path = Path(storage_path).resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[LocalStorageService] Initialized with storage_path={self.storage_path}")
    
    def _get_bucket_path(self, bucket_name: str) -> Path:
        """Get path for a bucket"""
        return self.storage_path / bucket_name
    
    def _get_object_path(self, bucket_name: str, object_key: str) -> Path:
        """Get full path for an object"""
        bucket_path = self._get_bucket_path(bucket_name)
        # Handle object keys with slashes (directories)
        object_path = bucket_path / object_key.lstrip('/')
        return object_path
    
    def _get_metadata_path(self, bucket_name: str, object_key: str) -> Path:
        """Get path for object metadata file"""
        object_path = self._get_object_path(bucket_name, object_key)
        return object_path.parent / f"{object_path.name}.metadata"
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure bucket directory exists"""
        bucket_path = self._get_bucket_path(bucket_name)
        bucket_path.mkdir(parents=True, exist_ok=True)
    
    def _calculate_etag(self, file_path: Path) -> str:
        """Calculate MD5 hash (ETag) for a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _save_metadata(self, bucket_name: str, object_key: str, metadata: Dict[str, Any]):
        """Save object metadata to a JSON file"""
        metadata_path = self._get_metadata_path(bucket_name, object_key)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, default=str)
    
    def _load_metadata(self, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """Load object metadata from JSON file"""
        metadata_path = self._get_metadata_path(bucket_name, object_key)
        if not metadata_path.exists():
            return None
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata for {bucket_name}/{object_key}: {e}")
            return None
    
    def put_object(
        self,
        bucket_name: str,
        object_key: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Put an object (upload)
        
        Args:
            bucket_name: Bucket name
            object_key: Object key (path)
            data: Object data as bytes
            content_type: Content type
            metadata: User metadata
            
        Returns:
            Dictionary with upload result
        """
        self._ensure_bucket_exists(bucket_name)
        object_path = self._get_object_path(bucket_name, object_key)
        
        # Ensure parent directory exists
        object_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write object data
        with open(object_path, 'wb') as f:
            f.write(data)
        
        # Calculate ETag
        etag = self._calculate_etag(object_path)
        
        # Get file stats
        stat = object_path.stat()
        
        # Save metadata
        metadata_dict = {
            'ContentType': content_type or 'application/octet-stream',
            'ContentLength': len(data),
            'LastModified': datetime.utcnow().isoformat(),
            'ETag': etag,
            'Metadata': metadata or {},
            'Size': stat.st_size,
        }
        self._save_metadata(bucket_name, object_key, metadata_dict)
        
        logger.info(f"[put_object] Uploaded {bucket_name}/{object_key}, size={len(data)}")
        
        return {
            'ETag': etag,
            'ContentLength': len(data),
        }
    
    def get_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """
        Get an object (download)
        
        Args:
            bucket_name: Bucket name
            object_key: Object key (path)
            
        Returns:
            Dictionary with object data and metadata
            
        Raises:
            FileNotFoundError: If object does not exist
        """
        object_path = self._get_object_path(bucket_name, object_key)
        
        if not object_path.exists():
            raise FileNotFoundError(f"Object {bucket_name}/{object_key} not found")
        
        # Load metadata
        metadata = self._load_metadata(bucket_name, object_key) or {}
        
        # Read object data
        with open(object_path, 'rb') as f:
            data = f.read()
        
        # Get last modified time from file system (more accurate than metadata)
        stat = object_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        return {
            'Body': data,
            'ContentType': metadata.get('ContentType', 'application/octet-stream'),
            'ContentLength': len(data),
            'LastModified': last_modified,
            'ETag': metadata.get('ETag', self._calculate_etag(object_path)),
            'Metadata': metadata.get('Metadata', {}),
        }
    
    def delete_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """
        Delete an object
        
        Args:
            bucket_name: Bucket name
            object_key: Object key (path)
            
        Returns:
            Dictionary with delete result
        """
        object_path = self._get_object_path(bucket_name, object_key)
        metadata_path = self._get_metadata_path(bucket_name, object_key)
        
        deleted = False
        if object_path.exists():
            object_path.unlink()
            deleted = True
        
        if metadata_path.exists():
            metadata_path.unlink()
        
        logger.info(f"[delete_object] Deleted {bucket_name}/{object_key}")
        
        return {
            'DeleteMarker': deleted,
        }
    
    def head_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """
        Get object metadata (HEAD request)
        
        Args:
            bucket_name: Bucket name
            object_key: Object key (path)
            
        Returns:
            Dictionary with object metadata
            
        Raises:
            FileNotFoundError: If object does not exist
        """
        object_path = self._get_object_path(bucket_name, object_key)
        
        if not object_path.exists():
            raise FileNotFoundError(f"Object {bucket_name}/{object_key} not found")
        
        # Load metadata
        metadata = self._load_metadata(bucket_name, object_key) or {}
        stat = object_path.stat()
        
        return {
            'ContentType': metadata.get('ContentType', 'application/octet-stream'),
            'ContentLength': stat.st_size,
            'LastModified': datetime.fromtimestamp(stat.st_mtime),
            'ETag': metadata.get('ETag', self._calculate_etag(object_path)),
            'Metadata': metadata.get('Metadata', {}),
        }
    
    def list_objects_v2(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List objects in a bucket (S3 ListObjectsV2 API)
        
        Args:
            bucket_name: Bucket name
            prefix: Optional prefix filter
            max_keys: Maximum number of keys to return
            continuation_token: Optional continuation token for pagination
            
        Returns:
            Dictionary with list of objects
        """
        bucket_path = self._get_bucket_path(bucket_name)
        
        if not bucket_path.exists():
            return {
                'IsTruncated': False,
                'KeyCount': 0,
                'Contents': [],
            }
        
        # Collect all objects
        objects = []
        prefix_path = bucket_path
        if prefix:
            prefix_path = bucket_path / prefix.lstrip('/')
        
        # Walk through directory structure
        if prefix_path.exists() and prefix_path.is_dir():
            for root, dirs, files in os.walk(prefix_path):
                for file in files:
                    if file.endswith('.metadata'):
                        continue
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(bucket_path)
                    object_key = str(rel_path).replace('\\', '/')
                    
                    # Check prefix match
                    if prefix and not object_key.startswith(prefix.lstrip('/')):
                        continue
                    
                    stat = file_path.stat()
                    metadata = self._load_metadata(bucket_name, object_key) or {}
                    
                    objects.append({
                        'Key': object_key,
                        'Size': stat.st_size,
                        'LastModified': datetime.fromtimestamp(stat.st_mtime),
                        'ETag': metadata.get('ETag', self._calculate_etag(file_path)),
                    })
        elif prefix_path.exists() and prefix_path.is_file():
            # Single file match
            rel_path = prefix_path.relative_to(bucket_path)
            object_key = str(rel_path).replace('\\', '/')
            stat = prefix_path.stat()
            metadata = self._load_metadata(bucket_name, object_key) or {}
            
            objects.append({
                'Key': object_key,
                'Size': stat.st_size,
                'LastModified': datetime.fromtimestamp(stat.st_mtime),
                'ETag': metadata.get('ETag', self._calculate_etag(prefix_path)),
            })
        
        # Sort by key
        objects.sort(key=lambda x: x['Key'])
        
        # Apply pagination
        start_index = 0
        if continuation_token:
            try:
                # Simple continuation token: index in the list
                start_index = int(continuation_token)
            except:
                pass
        
        end_index = start_index + max_keys
        paginated_objects = objects[start_index:end_index]
        is_truncated = end_index < len(objects)
        
        result = {
            'IsTruncated': is_truncated,
            'KeyCount': len(paginated_objects),
            'Contents': paginated_objects,
        }
        
        if is_truncated:
            result['NextContinuationToken'] = str(end_index)
        
        logger.info(f"[list_objects_v2] Found {len(paginated_objects)} objects in {bucket_name}")
        
        return result
    
    def object_exists(
        self,
        bucket_name: str,
        object_key: str
    ) -> bool:
        """
        Check if an object exists
        
        Args:
            bucket_name: Bucket name
            object_key: Object key (path)
            
        Returns:
            True if object exists, False otherwise
        """
        object_path = self._get_object_path(bucket_name, object_key)
        return object_path.exists() and object_path.is_file()

