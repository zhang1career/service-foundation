"""
MongoDB Atlas connection module for app_know.
Provides a configured MongoDriver instance for knowledge-related operations.
"""
import logging
import os
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class AtlasConfig:
    """Configuration for MongoDB Atlas connection."""

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        cluster: Optional[str] = None,
        db_name: Optional[str] = None,
    ):
        self.user = user or os.environ.get("MONGO_ATLAS_USER")
        self.password = password or os.environ.get("MONGO_ATLAS_PASS")
        self.host = host or os.environ.get("MONGO_ATLAS_HOST", "cluster.mongodb.net")
        self.cluster = cluster or os.environ.get("MONGO_ATLAS_CLUSTER", "cluster0")
        self.db_name = db_name or os.environ.get("MONGO_ATLAS_DB", "know")

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.user:
            raise ValueError("MONGO_ATLAS_USER is required")
        if not self.password:
            raise ValueError("MONGO_ATLAS_PASS is required")
        if not self.host:
            raise ValueError("MONGO_ATLAS_HOST is required")
        return True

    @property
    def uri(self) -> str:
        """Build MongoDB Atlas connection URI."""
        return (
            f"mongodb+srv://{self.user}:{self.password}@{self.cluster}.{self.host}/"
            f"?retryWrites=true&w=majority&appName=Cluster0"
        )


class AtlasClient:
    """MongoDB Atlas client with connection management."""

    def __init__(self, config: Optional[AtlasConfig] = None):
        self._config = config or AtlasConfig()
        self._client: Optional[MongoClient] = None
        self._db = None

    @property
    def config(self) -> AtlasConfig:
        return self._config

    def connect(self, timeout_ms: int = 5000) -> "AtlasClient":
        """
        Establish connection to MongoDB Atlas.

        Args:
            timeout_ms: Server selection timeout in milliseconds.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If configuration is invalid.
            ConnectionFailure: If connection fails.
        """
        self._config.validate()

        try:
            self._client = MongoClient(
                self._config.uri,
                tls=True,
                serverSelectionTimeoutMS=timeout_ms,
            )
            self._client.admin.command("ping")
            self._db = self._client[self._config.db_name]
            logger.info(f"Connected to MongoDB Atlas: {self._config.host}/{self._config.db_name}")
            return self
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB Atlas connection timeout: {e}")
            raise ConnectionFailure(f"Connection timeout: {e}") from e
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise

    def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB Atlas")

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if not self._client:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def ping(self) -> bool:
        """
        Ping the MongoDB server to check connectivity.

        Returns:
            True if ping succeeds.

        Raises:
            ConnectionFailure: If not connected or ping fails.
        """
        if not self._client:
            raise ConnectionFailure("Not connected to MongoDB Atlas")
        try:
            self._client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            raise ConnectionFailure(f"Ping failed: {e}") from e

    @property
    def client(self) -> MongoClient:
        """Get the underlying MongoClient instance."""
        if not self._client:
            raise ConnectionFailure("Not connected to MongoDB Atlas")
        return self._client

    @property
    def db(self):
        """Get the current database instance."""
        if not self._db:
            raise ConnectionFailure("Not connected to MongoDB Atlas")
        return self._db

    def get_collection(self, name: str):
        """Get a collection from the current database."""
        return self.db[name]

    def list_databases(self) -> list[str]:
        """List all available databases."""
        return self.client.list_database_names()

    def list_collections(self) -> list[str]:
        """List all collections in the current database."""
        return self.db.list_collection_names()

    def __enter__(self) -> "AtlasClient":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()


def get_atlas_client(
    db_name: Optional[str] = None,
    timeout_ms: int = 5000,
) -> AtlasClient:
    """
    Factory function to create and connect an AtlasClient.

    Args:
        db_name: Optional database name (defaults to MONGO_ATLAS_DB env var).
        timeout_ms: Connection timeout in milliseconds.

    Returns:
        Connected AtlasClient instance.
    """
    config = AtlasConfig(db_name=db_name)
    client = AtlasClient(config)
    return client.connect(timeout_ms=timeout_ms)
