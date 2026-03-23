"""
Invalidation repository - CRUD for Invalidation model
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app_cdn.enums.invalidation_status_enum import InvalidationStatusEnum
from app_cdn.models import Distribution, Invalidation
from app_cdn.utils.pagination import build_cloudfront_list_response

logger = logging.getLogger(__name__)


def get_invalidation_by_ids(distribution_id, invalidation_id) -> Optional[Invalidation]:
    """Get invalidation by distribution id and invalidation id."""
    try:
        _dist_id = int(distribution_id) if distribution_id is not None else None
        _inv_id = int(invalidation_id) if invalidation_id is not None else None
        if _dist_id is None or _inv_id is None:
            return None
        return Invalidation.objects.using("cdn_rw").filter(
            did_id=_dist_id, id=_inv_id
        ).first()
    except Exception as e:
        logger.exception("[get_invalidation_by_id] Error: %s", e)
        return None


def list_invalidations(
    distribution_id,
    marker: Optional[str] = None,
    max_items: int = 100,
) -> Dict[str, Any]:
    """
    List invalidations for a distribution.

    Returns:
        Dict with keys: Items (list), Quantity, NextMarker, IsTruncated
    """
    try:
        _dist_id = int(distribution_id) if distribution_id is not None else None
        if _dist_id is None:
            return {"Items": [], "Quantity": 0, "NextMarker": None, "IsTruncated": False}
        dist = Distribution.objects.using("cdn_rw").filter(id=_dist_id).first()
        if not dist:
            return {"Items": [], "Quantity": 0, "NextMarker": None, "IsTruncated": False}

        query = Invalidation.objects.using("cdn_rw").filter(
            did_id=_dist_id
        ).order_by("-ct")

        if marker:
            marker_inv = get_invalidation_by_ids(distribution_id, marker)
            if marker_inv:
                query = query.filter(ct__lt=marker_inv.ct)

        items = list(query[: max_items + 1])
        return build_cloudfront_list_response(
            items, max_items, lambda x: str(x.id)
        )
    except Exception as e:
        logger.exception("[list_invalidations] Error: %s", e)
        raise


def create_invalidation(
    distribution_id,
    paths: List[str],
    caller_reference: str,
) -> Invalidation:
    """Create a new invalidation."""
    try:
        _dist_id = int(distribution_id) if distribution_id is not None else None
        if _dist_id is None:
            raise ValueError("Distribution id is required")
        dist = Distribution.objects.using("cdn_rw").filter(id=_dist_id).first()
        if not dist:
            raise ValueError(f"Distribution not found: id={distribution_id}")

        # Check duplicate caller_reference
        existing = Invalidation.objects.using("cdn_rw").filter(
            did_id=_dist_id, caller_reference=caller_reference
        ).first()
        if existing:
            return existing  # CloudFront returns existing if same CallerReference

        return Invalidation.objects.using("cdn_rw").create(
            did_id=_dist_id,
            paths=json.dumps(paths),
            caller_reference=caller_reference,
            status=InvalidationStatusEnum.COMPLETED,  # Local replacement completes immediately
        )
    except ValueError:
        raise
    except Exception as e:
        logger.exception("[create_invalidation] Error: %s", e)
        raise
