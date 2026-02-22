"""
Repository for KnowledgeSummaryMapping CRUD operations.
"""
import logging
from typing import List, Optional, Tuple

from app_know.models.summary_mapping import KnowledgeSummaryMapping
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

_DB = "know_rw"


def get_mapping_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[str] = None,
) -> Optional[KnowledgeSummaryMapping]:
    """Get mapping by knowledge_id (kid), optionally filtered by app_id."""
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return None
    try:
        qs = KnowledgeSummaryMapping.objects.using(_DB).filter(kid=knowledge_id)
        if app_id is not None and str(app_id).strip():
            qs = qs.filter(app_id=str(app_id).strip())
        return qs.first()
    except Exception as e:
        logger.exception("[get_mapping_by_knowledge_id] Error: %s", e)
        return None


def get_mapping_by_summary_id(
    summary_id: str,
    app_id: Optional[str] = None,
) -> Optional[KnowledgeSummaryMapping]:
    """Get mapping by summary_id (sid), optionally filtered by app_id."""
    if not summary_id or not str(summary_id).strip():
        return None
    try:
        qs = KnowledgeSummaryMapping.objects.using(_DB).filter(sid=str(summary_id).strip())
        if app_id is not None and str(app_id).strip():
            qs = qs.filter(app_id=str(app_id).strip())
        return qs.first()
    except Exception as e:
        logger.exception("[get_mapping_by_summary_id] Error: %s", e)
        return None


def list_mappings(
    app_id: Optional[str] = None,
    knowledge_ids: Optional[List[int]] = None,
    offset: int = 0,
    limit: int = 100,
) -> Tuple[List[KnowledgeSummaryMapping], int]:
    """
    List mappings with optional filters.
    Returns (list of mappings, total count).
    """
    if offset is None or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    try:
        qs = KnowledgeSummaryMapping.objects.using(_DB).all().order_by("kid")
        if app_id is not None and str(app_id).strip():
            qs = qs.filter(app_id=str(app_id).strip())
        if knowledge_ids is not None and isinstance(knowledge_ids, list) and knowledge_ids:
            valid_ids = [i for i in knowledge_ids if isinstance(i, int) and i > 0]
            if valid_ids:
                qs = qs.filter(kid__in=valid_ids)
        total = qs.count()
        items = list(qs[offset : offset + limit])
        return items, total
    except Exception as e:
        logger.exception("[list_mappings] Error: %s", e)
        raise


def create_or_update_mapping(
    knowledge_id: int,
    summary_id: str,
    app_id: str,
) -> KnowledgeSummaryMapping:
    """
    Create or update a mapping (upsert by kid + app_id).
    Returns the mapping record.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if not summary_id or not str(summary_id).strip():
        raise ValueError("summary_id is required and cannot be empty")
    if not app_id or not str(app_id).strip():
        raise ValueError("app_id is required and cannot be empty")

    summary_id = str(summary_id).strip()
    app_id = str(app_id).strip()

    try:
        mapping, created = KnowledgeSummaryMapping.objects.using(_DB).get_or_create(
            kid=knowledge_id,
            app_id=app_id,
            defaults={"sid": summary_id},
        )
        if not created:
            mapping.sid = summary_id
            mapping.save(using=_DB)
        return mapping
    except Exception as e:
        logger.exception("[create_or_update_mapping] Error: %s", e)
        raise


def delete_mapping_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[str] = None,
) -> int:
    """
    Delete mapping(s) by knowledge_id (kid), optionally filtered by app_id.
    Returns number of deleted records.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return 0
    try:
        qs = KnowledgeSummaryMapping.objects.using(_DB).filter(kid=knowledge_id)
        if app_id is not None and str(app_id).strip():
            qs = qs.filter(app_id=str(app_id).strip())
        count, _ = qs.delete()
        return count
    except Exception as e:
        logger.exception("[delete_mapping_by_knowledge_id] Error: %s", e)
        raise


def get_knowledge_ids_by_summary_ids(
    summary_ids: List[str],
    app_id: Optional[str] = None,
) -> List[int]:
    """
    Get knowledge IDs by summary IDs (for query flow: Atlas -> MySQL -> Neo4j).
    Returns list of knowledge_ids (kid).
    """
    if not summary_ids or not isinstance(summary_ids, list):
        return []
    valid_ids = [str(s).strip() for s in summary_ids if s and str(s).strip()]
    if not valid_ids:
        return []
    try:
        qs = KnowledgeSummaryMapping.objects.using(_DB).filter(sid__in=valid_ids)
        if app_id is not None and str(app_id).strip():
            qs = qs.filter(app_id=str(app_id).strip())
        return list(qs.values_list("kid", flat=True))
    except Exception as e:
        logger.exception("[get_knowledge_ids_by_summary_ids] Error: %s", e)
        return []
