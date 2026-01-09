import logging

from app_oss.config import get_app_config
from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
from app_oss.services.local_storage_service import LocalStorageService
from common.components.singleton import Singleton

logger = logging.getLogger(__name__)


class OSSClient(Singleton):
    """OSS client wrapper for local storage with S3-compatible API"""
    
    def __init__(self):
        """Initialize OSS client with local storage configuration"""
        try:
            config = get_app_config()
            
            storage_path = config.get("storage_path")
            if not storage_path:
                raise ConfigurationErrorException(
                    "OSS_STORAGE_PATH is required"
                )
            self.local_storage = LocalStorageService(storage_path)
            self.default_bucket = config.get("bucket_name")
            logger.info("[OSSClient] Initialized with local storage at %s", storage_path)
            
        except Exception as e:
            logger.exception("[OSSClient] Failed to initialize: %s", str(e))
            raise ConfigurationErrorException(f"Failed to initialize OSS client: {str(e)}") from e
    
    def get_local_storage(self):
        """Get the local storage service instance"""
        return self.local_storage
    
    def get_default_bucket(self):
        """Get the default bucket name"""
        return self.default_bucket
