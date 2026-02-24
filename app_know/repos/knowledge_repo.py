"""
Knowledge repository: CRUD for KnowledgeEntity using know_rw database.
Generated.
"""
import logging
import time
from typing import Optional, List, Tuple

from app_know.models import Knowledge
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

_DB = "know_rw"


def _valid_entity_id(entity_id) -> bool:
    """Return True if entity_id is a positive integer."""
    if entity_id is None:
        return False
    if not isinstance(entity_id, int):
        return False
    return entity_id > 0


def get_knowledge_by_id(entity_id: int) -> Optional[Knowledge]:
    """Get knowledge entity by id. Returns None if not found or invalid id."""
    if not _valid_entity_id(entity_id):
        return None
    try:
        return Knowledge.objects.using(_DB).filter(id=entity_id).first()
    except Exception as e:
        logger.exception("[get_knowledge_by_id] Error: %s", e)
        return None


def list_knowledge(
    offset: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
) -> Tuple[List[Knowledge], int]:
    """
    List knowledge entities with optional filter by source_type.
    Returns (list of entities, total count).
    Raises ValueError for invalid offset or limit.
    """
    if offset is None or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    try:
        qs = Knowledge.objects.using(_DB).all().order_by("-ut")
        if source_type is not None and source_type.strip():
            qs = qs.filter(source_type=source_type.strip())
        total = qs.count()
        items = list(qs[offset : offset + limit])
        return items, total
    except Exception as e:
        logger.exception("[list_knowledge] Error: %s", e)
        raise


def create_knowledge(
    title: str,
    description: Optional[str] = None,
    content: Optional[str] = None,
    source_type: str = "unknown",
    ct: int = 0,
    ut: int = 0,
) -> Knowledge:
    """Create a knowledge entity. Raises ValueError on invalid input, re-raises DB errors."""
    if not title or not str(title).strip():
        raise ValueError("title is required and cannot be empty")
    try:
        if ct <= 0:
            ct = int(time.time() * 1000)
        if ut <= 0:
            ut = ct
        return Knowledge.objects.using(_DB).create(
            title=(title or "").strip(),
            description=description or "",
            content=content or "",
            source_type=(source_type or "unknown").strip() or "unknown",
            ct=ct,
            ut=ut,
        )
    except ValueError:
        raise
    except Exception as e:
        logger.exception("[create_knowledge] Error: %s", e)
        raise


def update_knowledge(entity: Knowledge, **kwargs) -> int:
    """Update entity fields. Returns number of rows updated. Raises on error."""
    if entity is None or not _valid_entity_id(getattr(entity, "id", None)):
        raise ValueError("entity must be a KnowledgeEntity with a valid id")
    try:
        return Knowledge.objects.using(_DB).filter(id=entity.id).update(**kwargs)
    except Exception as e:
        logger.exception("[update_knowledge] Error: %s", e)
        raise


def delete_knowledge(entity_id: int) -> bool:
    """Delete entity by id. Returns True if deleted, False if not found. Raises on DB error."""
    if not _valid_entity_id(entity_id):
        return False
    try:
        entity = get_knowledge_by_id(entity_id)
        if not entity:
            return False
        entity.delete(using=_DB)
        return True
    except Exception as e:
        logger.exception("[delete_knowledge] Error: %s", e)
        raise
