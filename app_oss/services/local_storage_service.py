"""
Local file storage service for S3-compatible object storage

This module provides a local file system implementation that mimics
AWS S3 API behavior, allowing seamless switching between local storage
and AWS S3.
"""
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
from app_oss.models.metadata import Metadata

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
        """Save object metadata to MySQL database (sf_oss.m table)"""
        try:
            Metadata.save_metadata_dict(bucket_name, object_key, metadata)
            logger.debug(f"[_save_metadata] Saved to sf_oss.m: {bucket_name}/{object_key}")
        except Exception as e:
            logger.error(
                f"[_save_metadata] Failed to save metadata for {bucket_name}/{object_key} to sf_oss.m: {e}",
                exc_info=True,
            )
            raise

    def _load_metadata(self, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """Load object metadata from MySQL database"""
        try:
            return Metadata.get_metadata_dict(bucket_name, object_key)
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
            ObjectNotFoundException: If object does not exist
        """
        object_path = self._get_object_path(bucket_name, object_key)

        if not object_path.exists():
            raise ObjectNotFoundException(f"Object {bucket_name}/{object_key} not found")

        # Load metadata
        metadata = self._load_metadata(bucket_name, object_key) or {}

        # Read object data
        with open(object_path, 'rb') as f:
            data = f.read()

        # Get last modified time from file system (more accurate than metadata)
        stat = object_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)

        logger.info(f"[get_object] Retrieved {bucket_name}/{object_key}, size={len(data)}")

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

        deleted = False
        if object_path.exists():
            object_path.unlink()
            deleted = True

        # Delete metadata from database
        try:
            Metadata.delete_metadata(bucket_name, object_key)
        except Exception as e:
            logger.warning(f"Failed to delete metadata for {bucket_name}/{object_key}: {e}")

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
            ObjectNotFoundException: If object does not exist
        """
        object_path = self._get_object_path(bucket_name, object_key)

        if not object_path.exists():
            raise ObjectNotFoundException(f"Object {bucket_name}/{object_key} not found")

        # Load metadata
        metadata = self._load_metadata(bucket_name, object_key) or {}
        stat = object_path.stat()

        logger.debug(f"[head_object] Metadata for {bucket_name}/{object_key}, size={stat.st_size}")

        return {
            'ContentType': metadata.get('ContentType', 'application/octet-stream'),
            'ContentLength': stat.st_size,
            'LastModified': datetime.fromtimestamp(stat.st_mtime),
            'ETag': metadata.get('ETag', self._calculate_etag(object_path)),
            'Metadata': metadata.get('Metadata', {}),
        }

    def _list_objects_raw(
            self,
            bucket_name: str,
            prefix: Optional[str] = None,
            delimiter: Optional[str] = None,
    ) -> tuple:
        """Collect objects (and common prefixes if delimiter). Returns (objects, common_prefixes)."""
        bucket_path = self._get_bucket_path(bucket_name)
        objects = []
        common_prefixes_set = set()

        if not bucket_path.exists():
            return objects, []

        prefix_norm = (prefix or '').lstrip('/')
        delim = delimiter or ''

        if delim:
            prefix_path = bucket_path / prefix_norm if prefix_norm else bucket_path
            if not prefix_path.exists():
                return objects, []
            if prefix_path.is_file():
                rel = str(prefix_path.relative_to(bucket_path)).replace('\\', '/')
                if not prefix_norm or rel.startswith(prefix_norm):
                    self._append_result(objects, prefix_path, bucket_name, rel)
                return objects, []
            for item in prefix_path.iterdir():
                rel = str(item.relative_to(bucket_path)).replace('\\', '/')
                if prefix_norm and not rel.startswith(prefix_norm):
                    continue
                if item.is_dir():
                    cp = rel + delim if not rel.endswith(delim) else rel
                    common_prefixes_set.add(cp)
                elif item.is_file():
                    self._append_result(objects, item, bucket_name, rel)
        else:
            prefix_path = bucket_path / prefix_norm if prefix_norm else bucket_path
            if prefix_path.exists() and prefix_path.is_dir():
                for root, dirs, files in os.walk(prefix_path):
                    for file in files:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(bucket_path)
                        object_key = str(rel_path).replace('\\', '/')
                        if prefix_norm and not object_key.startswith(prefix_norm):
                            continue
                        self._append_result(objects, file_path, bucket_name, object_key)
            elif prefix_path.exists() and prefix_path.is_file():
                rel_path = prefix_path.relative_to(bucket_path)
                object_key = str(rel_path).replace('\\', '/')
                self._append_result(objects, prefix_path, bucket_name, object_key)

        objects.sort(key=lambda x: x['Key'])
        common_prefixes = sorted([{'Prefix': p} for p in common_prefixes_set], key=lambda x: x['Prefix'])
        return objects, common_prefixes

    def list_objects_v2(
            self,
            bucket_name: str,
            prefix: Optional[str] = None,
            max_keys: int = 1000,
            continuation_token: Optional[str] = None,
            start_after: Optional[str] = None,
            delimiter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List objects in a bucket (S3 ListObjectsV2 API)."""
        objects, common_prefixes = self._list_objects_raw(bucket_name, prefix, delimiter)

        all_items = objects + common_prefixes
        all_items.sort(key=lambda x: x.get('Key', x.get('Prefix', '')))

        if start_after:
            all_items = [x for x in all_items if (x.get('Key') or x.get('Prefix', '')) > start_after]

        start_index = 0
        if continuation_token:
            try:
                start_index = int(continuation_token)
            except (ValueError, TypeError):
                pass

        start_index = min(start_index, len(all_items))
        end_index = min(start_index + max_keys, len(all_items))
        page = all_items[start_index:end_index]
        contents = [x for x in page if 'Key' in x]
        common = [x for x in page if 'Prefix' in x]
        is_truncated = end_index < len(all_items)

        result = {
            'IsTruncated': is_truncated,
            'KeyCount': len(contents) + len(common),
            'Contents': contents,
            'CommonPrefixes': common,
        }
        if is_truncated:
            result['NextContinuationToken'] = str(end_index)

        logger.info(f"[list_objects_v2] Found {len(contents)} objects in {bucket_name}")
        return result

    def list_objects_v1(
            self,
            bucket_name: str,
            prefix: Optional[str] = None,
            delimiter: Optional[str] = None,
            max_keys: int = 1000,
            marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List objects in a bucket (S3 ListObjects V1 API)."""
        objects, common_prefixes = self._list_objects_raw(bucket_name, prefix, delimiter)

        all_items = objects + common_prefixes
        all_items.sort(key=lambda x: x.get('Key', x.get('Prefix', '')))

        start_index = 0
        if marker:
            for i, item in enumerate(all_items):
                k = item.get('Key', item.get('Prefix', ''))
                if k > marker:
                    start_index = i
                    break

        end_index = min(start_index + max_keys, len(all_items))
        page = all_items[start_index:end_index]
        contents = [x for x in page if 'Key' in x]
        common = [x for x in page if 'Prefix' in x]
        is_truncated = end_index < len(all_items)
        next_marker = ''
        if is_truncated and page:
            last = page[-1]
            next_marker = last.get('Key', last.get('Prefix', ''))

        return {
            'Marker': marker or '',
            'IsTruncated': is_truncated,
            'Contents': contents,
            'CommonPrefixes': common,
            'NextMarker': next_marker,
        }

    def list_buckets(self) -> list:
        """List all bucket names (directories under storage path)."""
        if not self.storage_path.exists():
            return []
        return [
            d.name for d in self.storage_path.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

    def delete_objects(
            self,
            bucket_name: str,
            keys: list,
    ) -> Dict[str, Any]:
        """Delete multiple objects. Returns deleted and errors lists."""
        deleted = []
        errors = []
        for key in keys:
            try:
                self.delete_object(bucket_name, key)
                deleted.append({'Key': key})
            except Exception as e:
                errors.append({'Key': key, 'Code': 'InternalError', 'Message': str(e)})
        return {'Deleted': deleted, 'Errors': errors}

    def _append_result(self, objects, file_path, bucket_name, object_key):
        stat = file_path.stat()
        metadata = self._load_metadata(bucket_name, object_key) or {}
        objects.append({
            'Key': object_key,
            'Size': stat.st_size,
            'LastModified': datetime.fromtimestamp(stat.st_mtime),
            'ETag': metadata.get('ETag', self._calculate_etag(file_path)),
        })

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
