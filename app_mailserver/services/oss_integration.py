"""
OSS integration service for mail attachments

This service provides methods to upload, download, and delete mail attachments
using the app_oss S3-compatible API.
"""
import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any

from app_mailserver.config import get_app_config
from common.exceptions.configuration_error_exception import ConfigurationErrorException

logger = logging.getLogger(__name__)


class OSSIntegrationService:
    """OSS integration service for mail attachments"""

    def __init__(self):
        """Initialize OSS client with configuration"""
        try:
            config = get_app_config()
            self.bucket = config.get("oss_bucket", "mail-attachments")
            endpoint_url = config.get("oss_endpoint", "http://localhost:8000/api/oss")

            # Create S3 client pointing to app_oss endpoint
            # Use dummy credentials since app_oss doesn't require real AWS credentials
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy',
                region_name='us-east-1',
                config=Config(signature_version='s3v4')
            )

            logger.info(f"[OSSIntegrationService] Initialized with bucket={self.bucket}, endpoint={endpoint_url}")

        except Exception as e:
            logger.exception(f"[OSSIntegrationService] Failed to initialize: {e}")
            raise ConfigurationErrorException(f"Failed to initialize OSS integration: {str(e)}") from e

    def upload_attachment(
            self,
            key: str,
            data: bytes,
            content_type: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload an attachment to OSS
        
        Args:
            key: Object key (path) in OSS
            data: Attachment data as bytes
            content_type: MIME type of the attachment
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with upload result (ETag, etc.)
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            # Convert metadata to x-amz-meta-* format
            if metadata:
                extra_args['Metadata'] = metadata

            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                **extra_args
            )

            logger.info(f"[upload_attachment] Uploaded {self.bucket}/{key}, size={len(data)}")

            return {
                'bucket': self.bucket,
                'key': key,
                'size': len(data)
            }

        except ClientError as e:
            logger.error(f"[upload_attachment] Failed to upload {self.bucket}/{key}: {e}")
            raise
        except Exception as e:
            logger.exception(f"[upload_attachment] Unexpected error uploading {self.bucket}/{key}: {e}")
            raise

    def download_attachment(self, key: str) -> bytes:
        """
        Download an attachment from OSS
        
        Args:
            key: Object key (path) in OSS
            
        Returns:
            Attachment data as bytes
            
        Raises:
            ClientError: If object not found or other S3 error
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )

            data = response['Body'].read()
            logger.info(f"[download_attachment] Downloaded {self.bucket}/{key}, size={len(data)}")

            return data

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.error(f"[download_attachment] Attachment not found: {self.bucket}/{key}")
            else:
                logger.error(f"[download_attachment] Failed to download {self.bucket}/{key}: {e}")
            raise
        except Exception as e:
            logger.exception(f"[download_attachment] Unexpected error downloading {self.bucket}/{key}: {e}")
            raise

    def delete_attachment(self, key: str) -> bool:
        """
        Delete an attachment from OSS
        
        Args:
            key: Object key (path) in OSS
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )

            logger.info(f"[delete_attachment] Deleted {self.bucket}/{key}")
            return True

        except ClientError as e:
            logger.error(f"[delete_attachment] Failed to delete {self.bucket}/{key}: {e}")
            return False
        except Exception as e:
            logger.exception(f"[delete_attachment] Unexpected error deleting {self.bucket}/{key}: {e}")
            return False

    def get_attachment_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get attachment metadata from OSS
        
        Args:
            key: Object key (path) in OSS
            
        Returns:
            Dictionary with metadata, or None if not found
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=key
            )

            metadata = {
                'ContentType': response.get('ContentType', 'application/octet-stream'),
                'ContentLength': response.get('ContentLength', 0),
                'LastModified': response.get('LastModified'),
                'ETag': response.get('ETag', '').strip('"'),
                'Metadata': response.get('Metadata', {})
            }

            return metadata

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                logger.warning(f"[get_attachment_metadata] Attachment not found: {self.bucket}/{key}")
            else:
                logger.error(f"[get_attachment_metadata] Failed to get metadata for {self.bucket}/{key}: {e}")
            return None
        except Exception as e:
            logger.exception(
                f"[get_attachment_metadata] Unexpected error getting metadata for {self.bucket}/{key}: {e}")
            return None


# Singleton instance
_oss_service = None


def get_oss_service() -> OSSIntegrationService:
    """Get singleton OSS integration service instance"""
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSIntegrationService()
    return _oss_service
