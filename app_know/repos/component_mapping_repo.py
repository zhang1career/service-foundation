"""
Repository for KnowledgeComponentMapping CRUD operations.
Uses raw SQL because table y has composite primary key (kid, cid, app_id).
"""
import logging
from typing import Any, Dict, List, Optional

from django.db import connections

logger = logging.getLogger(__name__)

_DB = "know_rw"

# Component type constants
TYPE_SUBJECT = 0
TYPE_OBJECT = 1


def create_mapping(
    knowledge_id: int,
    component_id: str,
    app_id: int,
    component_type: int = TYPE_SUBJECT,
) -> None:
    """
    Create a knowledge-component mapping. Uses INSERT IGNORE to avoid duplicates.
    Table y has composite primary key (kid, cid, app_id).
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if not component_id or not str(component_id).strip():
        raise ValueError("component_id is required and cannot be empty")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if component_type not in (TYPE_SUBJECT, TYPE_OBJECT):
        raise ValueError("component_type must be 0 (subject) or 1 (object)")

    cid = str(component_id).strip()

    try:
        with connections[_DB].cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO y (kid, cid, app_id, type) VALUES (%s, %s, %s, %s)",
                [knowledge_id, cid, app_id, component_type],
            )
    except Exception as e:
        logger.exception("[create_mapping] Error: %s", e)
        raise


def get_mappings_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[int] = None,
    component_type: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get component mappings by knowledge_id (kid).
    Optionally filter by app_id and component_type (0=subject, 1=object).
    Returns list of dicts with kid, cid, app_id, type.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return []
    try:
        sql = "SELECT kid, cid, app_id, type FROM y WHERE kid = %s"
        params: List[Any] = [knowledge_id]
        if app_id is not None and isinstance(app_id, int) and app_id >= 0:
            sql += " AND app_id = %s"
            params.append(app_id)
        if component_type is not None and component_type in (TYPE_SUBJECT, TYPE_OBJECT):
            sql += " AND type = %s"
            params.append(component_type)
        sql += " ORDER BY kid, cid, app_id"

        with connections[_DB].cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.exception("[get_mappings_by_knowledge_id] Error: %s", e)
        return []


def get_cids_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[int] = None,
    component_type: Optional[int] = None,
) -> List[str]:
    """
    Get unique component IDs (cids) by knowledge_id.
    Optionally filter by app_id and component_type.
    """
    mappings = get_mappings_by_knowledge_id(knowledge_id, app_id, component_type)
    seen = set()
    result = []
    for m in mappings:
        cid = m.get("cid")
        if cid and cid not in seen:
            seen.add(cid)
            result.append(cid)
    return result
