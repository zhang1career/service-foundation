"""
Insight repository: CRUD for Insight model.
"""
import logging
from typing import List, Optional, Tuple

from app_know.models import Insight
from common.consts.query_const import LIMIT_LIST
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)

_DB = "know_rw"


def create_insight(
        content: str,
        type: int = 1,  # INSIGHT_PATH_REASONING
        status: int = 0,
        perspective: Optional[int] = None,
) -> Insight:
    """Create an insight. Returns the created Insight."""
    content = (content or "").strip()
    if not content:
        raise ValueError("content is required and cannot be empty")
    now_ms = get_now_timestamp_ms()
    i = Insight(
        content=content,
        type=type if type is not None else 1,
        status=status,
        perspective=perspective,
        ct=now_ms,
        ut=now_ms,
    )
    i.save(using=_DB)
    return i


def get_insight_by_id(iid: int) -> Optional[Insight]:
    """Get insight by id."""
    if iid is None or not isinstance(iid, int) or iid <= 0:
        return None
    try:
        return Insight.objects.using(_DB).filter(id=iid).first()
    except Exception as e:
        logger.exception("[get_insight_by_id] Error: %s", e)
        return None


def list_insights(
        perspective: Optional[int] = None,
        type: Optional[int] = None,
        status: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
) -> Tuple[List[Insight], int]:
    """List insights with optional filters. Returns (list, total)."""
    if limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
    qs = Insight.objects.using(_DB).all().order_by("-ut")
    if perspective is not None:
        qs = qs.filter(perspective=perspective)
    if type is not None:
        qs = qs.filter(type=type)
    if status is not None:
        qs = qs.filter(status=status)
    total = qs.count()
    items = list(qs[offset: offset + limit])
    return items, total


def update_insight(iid: int, **kwargs) -> bool:
    """Update insight by id. Returns True if updated."""
    if iid is None or not isinstance(iid, int) or iid <= 0:
        return False
    allowed = {"content", "type", "status", "perspective"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["ut"] = get_now_timestamp_ms()
    try:
        updated = Insight.objects.using(_DB).filter(id=iid).update(**updates)
        return updated > 0
    except Exception as e:
        logger.exception("[update_insight] Error: %s", e)
        return False


def delete_insight(iid: int) -> bool:
    """Delete insight by id. Returns True if deleted."""
    if iid is None or not isinstance(iid, int) or iid <= 0:
        return False
    try:
        count, _ = Insight.objects.using(_DB).filter(id=iid).delete()
        return count > 0
    except Exception as e:
        logger.exception("[delete_insight] Error: %s", e)
        return False
