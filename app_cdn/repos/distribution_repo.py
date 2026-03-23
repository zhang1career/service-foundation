"""
Distribution repository - CRUD for Distribution model
"""
import json
import logging
from typing import Any, Dict, Optional

from app_cdn.models import Distribution
from app_cdn.utils.pagination import build_cloudfront_list_response

logger = logging.getLogger(__name__)


def get_distribution_by_id(distribution_id) -> Optional[Distribution]:
    """Get distribution by primary key id."""
    try:
        _id = int(distribution_id) if distribution_id is not None else None
        if _id is None:
            return None
        return Distribution.objects.using("cdn_rw").filter(id=_id).first()
    except Exception as e:
        logger.exception("[get_distribution_by_id] Error: %s", e)
        return None


def list_distributions(
    marker: Optional[str] = None,
    max_items: int = 100,
) -> Dict[str, Any]:
    """
    List distributions with pagination.

    Returns:
        Dict with keys: Items (list), Quantity, NextMarker, IsTruncated
    """
    try:
        query = Distribution.objects.using("cdn_rw").order_by("ct")

        if marker:
            # Get distributions after marker (by id)
            marker_dist = get_distribution_by_id(marker)
            if marker_dist:
                query = query.filter(ct__gt=marker_dist.ct)

        items = list(query[: max_items + 1])
        return build_cloudfront_list_response(
            items, max_items, lambda x: str(x.id)
        )
    except Exception as e:
        logger.exception("[list_distributions] Error: %s", e)
        raise


def create_distribution(
    domain_name: str,
    origin_config: Optional[Dict] = None,
    aliases: Optional[list] = None,
    enabled: bool = True,
    comment: str = "",
) -> Distribution:
    """Create a new distribution."""
    try:
        origin_config = origin_config or {}
        aliases = aliases or []

        return Distribution.objects.using("cdn_rw").create(
            domain_name=domain_name,
            origin_config=json.dumps(origin_config),
            aliases=json.dumps(aliases),
            enabled=enabled,
            comment=comment or "",
        )
    except Exception as e:
        logger.exception("[create_distribution] Error: %s", e)
        raise


def update_distribution(
    distribution_id,
    origin_config: Optional[Dict] = None,
    aliases: Optional[list] = None,
    enabled: Optional[bool] = None,
    comment: Optional[str] = None,
) -> Optional[Distribution]:
    """Update distribution. Returns updated instance or None."""
    try:
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return None

        if origin_config is not None:
            dist.origin_config = json.dumps(origin_config)
        if aliases is not None:
            dist.aliases = json.dumps(aliases)
        if enabled is not None:
            dist.enabled = enabled
        if comment is not None:
            dist.comment = comment

        dist.save(using="cdn_rw")
        return dist
    except Exception as e:
        logger.exception("[update_distribution] Error: %s", e)
        raise


def delete_distribution(distribution_id) -> bool:
    """Delete distribution. Returns True if deleted."""
    try:
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return False
        dist.delete(using="cdn_rw")
        return True
    except Exception as e:
        logger.exception("[delete_distribution] Error: %s", e)
        raise
