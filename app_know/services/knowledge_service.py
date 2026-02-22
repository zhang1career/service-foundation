"""
Knowledge service: validation and CRUD business logic for knowledge metadata.
Generated.
"""
import logging
import time
from typing import Any, Dict, Optional

from app_know.models import Knowledge
from app_know.repos import (
    get_knowledge_by_id,
    list_knowledge,
    create_knowledge,
    update_knowledge,
    delete_knowledge,
)
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

# Max length for title and source_type to match model
TITLE_MAX_LEN = 512
SOURCE_TYPE_MAX_LEN = 64


def _validate_entity_id(entity_id) -> None:
    """Raise ValueError if entity_id is not a positive integer."""
    if entity_id is None:
        raise ValueError("entity_id is required")
    if not isinstance(entity_id, int):
        raise ValueError("entity_id must be an integer")
    if entity_id <= 0:
        raise ValueError("entity_id must be a positive integer")


def _entity_to_dict(entity: Knowledge) -> Dict[str, Any]:
    """Convert KnowledgeEntity to API dict."""
    return {
        "id": entity.id,
        "title": entity.title,
        "description": entity.description or "",
        "source_type": entity.source_type,
        "metadata": entity.metadata,
        "ct": entity.ct,
        "ut": entity.ut,
    }


class KnowledgeService(Singleton):
    """Service for knowledge metadata CRUD with validation."""

    def list_knowledge(
        self,
        offset: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List knowledge entities with pagination.
        Returns dict with data, total_num, next_offset.
        """
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit <= 0 or limit > LIMIT_LIST:
            raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
        items, total = list_knowledge(offset=offset, limit=limit, source_type=source_type)
        next_offset = offset + len(items) if (offset + len(items)) < total else None
        return {
            "data": [_entity_to_dict(e) for e in items],
            "total_num": total,
            "next_offset": next_offset,
        }

    def get_knowledge(self, entity_id: int) -> Dict[str, Any]:
        """Get one entity by id. Raises ValueError if invalid id or not found."""
        _validate_entity_id(entity_id)
        entity = get_knowledge_by_id(entity_id)
        if not entity:
            raise ValueError(f"Knowledge entity with id {entity_id} not found")
        return _entity_to_dict(entity)

    def create_knowledge(
        self,
        title: str,
        description: Optional[str] = None,
        source_type: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create entity. Validates title (required). Raises ValueError on validation error."""
        t = (str(title).strip() if title is not None else "")
        if not t:
            raise ValueError("title is required and cannot be empty")
        if len(t) > TITLE_MAX_LEN:
            raise ValueError(f"title must be at most {TITLE_MAX_LEN} characters")
        st = (str(source_type).strip() if source_type is not None else "") or "unknown"
        if len(st) > SOURCE_TYPE_MAX_LEN:
            raise ValueError(f"source_type must be at most {SOURCE_TYPE_MAX_LEN} characters")
        desc_val = description if description is not None else ""
        desc_str = str(desc_val).strip() if not isinstance(desc_val, str) else desc_val.strip()
        now_ms = int(time.time() * 1000)
        entity = create_knowledge(
            title=t,
            description=desc_str or None,
            source_type=st,
            metadata=metadata,
            ct=now_ms,
            ut=now_ms,
        )
        return _entity_to_dict(entity)

    def update_knowledge(
        self,
        entity_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        source_type: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update entity. Raises ValueError if invalid id, not found, or validation fails."""
        _validate_entity_id(entity_id)
        entity = get_knowledge_by_id(entity_id)
        if not entity:
            raise ValueError(f"Knowledge entity with id {entity_id} not found")
        updates = {}
        if title is not None:
            t = (str(title) if not isinstance(title, str) else title).strip()
            if not t:
                raise ValueError("title cannot be empty")
            if len(t) > TITLE_MAX_LEN:
                raise ValueError(f"title must be at most {TITLE_MAX_LEN} characters")
            updates["title"] = t
        if description is not None:
            d = str(description) if not isinstance(description, str) else description
            updates["description"] = d.strip() or ""
        if source_type is not None:
            st = (str(source_type) if not isinstance(source_type, str) else source_type).strip() or "unknown"
            if len(st) > SOURCE_TYPE_MAX_LEN:
                raise ValueError(f"source_type must be at most {SOURCE_TYPE_MAX_LEN} characters")
            updates["source_type"] = st
        if metadata is not None:
            updates["metadata"] = metadata
        if updates:
            updates["ut"] = int(time.time() * 1000)
            update_knowledge(entity, **updates)
            entity = get_knowledge_by_id(entity_id)
        return _entity_to_dict(entity)

    def delete_knowledge(self, entity_id: int) -> None:
        """Delete entity and sync: remove summaries for this knowledge_id. Raises ValueError if invalid id or not found."""
        _validate_entity_id(entity_id)
        deleted = delete_knowledge(entity_id)
        if not deleted:
            raise ValueError(f"Knowledge entity with id {entity_id} not found")
        # Keep summaries in sync: remove MongoDB summaries for this knowledge_id
        try:
            from app_know.services.summary_service import SummaryService
            SummaryService().delete_summaries_for_knowledge(knowledge_id=entity_id)
        except Exception as e:
            logger.warning("[delete_knowledge] Failed to delete summaries for knowledge_id=%s: %s", entity_id, e)
