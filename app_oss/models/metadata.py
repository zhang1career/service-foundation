import json
from django.db import models

from app_oss.enums.content_type_enum import ContentTypeEnum


class Metadata(models.Model):
    """OSS object metadata model stored in MySQL database"""
    
    # Composite primary key: bucket_name + object_key
    bucket_name = models.CharField(max_length=255, db_index=True)
    object_key = models.CharField(max_length=1024, db_index=True)
    
    # Object metadata fields
    # content_type stores ContentTypeEnum value (integer id)
    content_type = models.IntegerField(default=ContentTypeEnum.APPLICATION_OCTET_STREAM.value)
    content_length = models.BigIntegerField(default=0)
    etag = models.CharField(max_length=64)
    size = models.BigIntegerField(default=0)
    
    # User-defined metadata stored as TEXT (JSON string)
    metadata = models.TextField(blank=True, null=True)
    
    # Update time: Unix timestamp in milliseconds
    ut = models.BigIntegerField(default=0)
    
    class Meta:
        db_table = "m"
        # Composite unique constraint on bucket_name and object_key
        unique_together = [['bucket_name', 'object_key']]
        # Use oss database
        app_label = 'app_oss'
    
    def __str__(self):
        return f"{self.bucket_name}/{self.object_key}"
    
    @classmethod
    def get_metadata_dict(cls, bucket_name: str, object_key: str) -> dict:
        """
        Get metadata as dictionary format compatible with file-based storage
        
        Returns:
            Dictionary with metadata fields, or None if not found
        """
        try:
            meta = cls.objects.using('oss_rw').get(
                bucket_name=bucket_name,
                object_key=object_key
            )
            # Convert content_type enum id to MIME type string
            try:
                content_type_enum = ContentTypeEnum(meta.content_type)
                content_type_str = content_type_enum.to_mime_type()
            except (ValueError, AttributeError):
                # Fallback to default if enum value is invalid
                content_type_str = ContentTypeEnum.APPLICATION_OCTET_STREAM.to_mime_type()
            
            # Convert Unix timestamp (milliseconds) to ISO format string
            from datetime import datetime, timezone
            if meta.ut and meta.ut > 0:
                last_modified = datetime.fromtimestamp(meta.ut / 1000.0, tz=timezone.utc)
                last_modified_str = last_modified.isoformat()
            else:
                last_modified_str = datetime.utcnow().isoformat()
            
            # Parse metadata from TEXT (JSON string) to dict
            metadata_dict = {}
            if meta.metadata:
                try:
                    metadata_dict = json.loads(meta.metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata_dict = {}
            
            return {
                'ContentType': content_type_str,
                'ContentLength': meta.content_length,
                'LastModified': last_modified_str,
                'ETag': meta.etag,
                'Metadata': metadata_dict,
                'Size': meta.size,
            }
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def save_metadata_dict(cls, bucket_name: str, object_key: str, metadata_dict: dict):
        """
        Save metadata from dictionary format
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            metadata_dict: Dictionary with metadata fields
        """
        # Convert MIME type string to enum id
        content_type_str = metadata_dict.get('ContentType', 'application/octet-stream')
        content_type_enum = ContentTypeEnum.from_mime_type(content_type_str)
        
        # Convert metadata dict to JSON string
        user_metadata = metadata_dict.get('Metadata', {})
        metadata_text = ''
        if user_metadata:
            try:
                metadata_text = json.dumps(user_metadata)
            except (TypeError, ValueError):
                metadata_text = ''
        
        # Convert LastModified to Unix timestamp (milliseconds)
        from datetime import datetime, timezone
        ut_timestamp = 0
        if 'LastModified' in metadata_dict:
            last_modified = metadata_dict['LastModified']
            if isinstance(last_modified, str):
                # Parse ISO format string
                try:
                    dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    # Convert to UTC if timezone-aware, otherwise assume UTC
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    ut_timestamp = int(dt.timestamp() * 1000)
                except:
                    ut_timestamp = int(datetime.utcnow().timestamp() * 1000)
            elif isinstance(last_modified, datetime):
                # Already a datetime object
                if last_modified.tzinfo is None:
                    last_modified = last_modified.replace(tzinfo=timezone.utc)
                else:
                    last_modified = last_modified.astimezone(timezone.utc)
                ut_timestamp = int(last_modified.timestamp() * 1000)
        else:
            # Use current time if not provided
            ut_timestamp = int(datetime.utcnow().timestamp() * 1000)
        
        defaults = {
            'content_type': content_type_enum.value,  # Store enum id
            'content_length': metadata_dict.get('ContentLength', 0),
            'etag': metadata_dict.get('ETag', ''),
            'size': metadata_dict.get('Size', 0),
            'metadata': metadata_text,  # Store as JSON string
            'ut': ut_timestamp,  # Store Unix timestamp in milliseconds
        }
        
        cls.objects.using('oss_rw').update_or_create(
            bucket_name=bucket_name,
            object_key=object_key,
            defaults=defaults
        )
    
    @classmethod
    def delete_metadata(cls, bucket_name: str, object_key: str):
        """
        Delete metadata for an object
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
        """
        cls.objects.using('oss_rw').filter(
            bucket_name=bucket_name,
            object_key=object_key
        ).delete()
