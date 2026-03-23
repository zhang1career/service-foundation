"""
CDN provider protocol - CloudFront-compatible interface

Defines the abstract contract for CDN operations. Implementations include:
- app_cdn: Local replacement (proxy to OSS/origin)
- Future: boto3 CloudFront adapter
"""
from typing import Any, Dict, List, Optional, Protocol


class CdnProviderProtocol(Protocol):
    """
    Protocol for CDN operations compatible with Amazon CloudFront.
    Used for dependency injection and swapping implementations.
    """

    def list_distributions(
        self,
        marker: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List distributions with pagination."""
        ...

    def get_distribution(self, distribution_id: str) -> Optional[Dict[str, Any]]:
        """Get distribution by ID."""
        ...

    def get_distribution_config(self, distribution_id: str) -> Optional[Dict[str, Any]]:
        """Get distribution configuration."""
        ...

    def create_distribution(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new distribution."""
        ...

    def update_distribution(
        self, distribution_id: str, config: Dict[str, Any], if_match: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update distribution configuration."""
        ...

    def delete_distribution(
        self, distribution_id: str, if_match: Optional[str] = None
    ) -> bool:
        """Delete a distribution."""
        ...

    def create_invalidation(
        self, distribution_id: str, paths: List[str], caller_reference: str
    ) -> Dict[str, Any]:
        """Create cache invalidation for paths."""
        ...

    def list_invalidations(
        self,
        distribution_id: str,
        marker: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List invalidations for a distribution."""
        ...

    def get_invalidation(
        self, distribution_id: str, invalidation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get invalidation by ID."""
        ...
