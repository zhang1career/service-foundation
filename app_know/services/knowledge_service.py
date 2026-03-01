"""
Knowledge service: validation and CRUD business logic for knowledge entities.
Generated.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app_know.models import Knowledge
from app_know.repos import (
    get_knowledge_by_id,
    get_knowledge_by_ids,
    list_knowledge,
    create_knowledge,
    update_knowledge,
    delete_knowledge,
)
from app_know.repos.summary_repo import search_summaries_by_vector_filtered
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


def _entity_to_dict(entity: Knowledge, similarity: Optional[float] = None) -> Dict[str, Any]:
    """Convert KnowledgeEntity to API dict. Optionally include similarity (0-1) when filtered by summary."""
    out = {
        "id": entity.id,
        "title": entity.title,
        "description": entity.description or "",
        "content": entity.content or "",
        "source_type": entity.source_type,
        "ct": entity.ct,
        "ut": entity.ut,
    }
    if similarity is not None:
        out["similarity"] = round(similarity, 4)
    return out


class KnowledgeService(Singleton):
    """Service for knowledge CRUD with validation."""

    def list_knowledge(
        self,
        offset: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        summary: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List knowledge entities with pagination.
        When title is provided: left-aligned prefix match on title field (title takes priority over summary).
        When summary is provided (and title is not): semantic search via Atlas knowledge_summaries,
        return top 5 with similarity.
        Otherwise: standard list with offset/limit/source_type.
        Returns dict with data, total_num, next_offset, filtered_by_summary (bool).
        """
        if title is not None and str(title).strip():
            t = str(title).strip()
            if offset < 0:
                raise ValueError("offset must be >= 0")
            if limit <= 0 or limit > LIMIT_LIST:
                raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
            items, total = list_knowledge(offset=offset, limit=limit, source_type=source_type, title=t)
            next_offset = offset + len(items) if (offset + len(items)) < total else None
            return {
                "data": [_entity_to_dict(e) for e in items],
                "total_num": total,
                "next_offset": next_offset,
                "filtered_by_summary": False,
            }
        if summary is not None and str(summary).strip():
            # Filter by summary: vector search -> get kid list -> fetch from MySQL
            q = str(summary).strip()
            logger.debug("[list_knowledge] summary filter path: query=%r", q[:80])
            try:
                vector_results = search_summaries_by_vector_filtered(query=q, app_id=0, top_k=5)
                logger.debug("[list_knowledge] vector_results count=%s, kids=%s", len(vector_results), [r.get("kid") for r in vector_results[:5]])
            except Exception as e:
                logger.warning("[list_knowledge] summary vector search failed: %s", e)
                return {
                    "data": [],
                    "total_num": 0,
                    "next_offset": None,
                    "filtered_by_summary": True,
                }
            if not vector_results:
                return {
                    "data": [],
                    "total_num": 0,
                    "next_offset": None,
                    "filtered_by_summary": True,
                }
            kid_to_score = {r["kid"]: r.get("score", 0.0) for r in vector_results}
            kids = [r["kid"] for r in vector_results]
            entities = get_knowledge_by_ids(kids)
            logger.debug("[list_knowledge] get_knowledge_by_ids: requested=%s, got=%s", kids, [e.id for e in entities])
            items_with_sim = [
                _entity_to_dict(e, similarity=kid_to_score.get(e.id))
                for e in entities
                if e.id in kid_to_score
            ]
            return {
                "data": items_with_sim,
                "total_num": len(items_with_sim),
                "next_offset": None,
                "filtered_by_summary": True,
            }
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
            "filtered_by_summary": False,
        }

    def query_knowledge_some_like(self, summary: str) -> List[Dict[str, Any]]:
        """
        Query knowledge by summary (semantic search).
        Returns list of up to 5 knowledge dicts with similarity, ordered by similarity desc.
        Returns empty list if not found.
        """
        q = (str(summary) or "").strip()
        if not q:
            return []
        try:
            vector_results = search_summaries_by_vector_filtered(query=q, app_id=0, top_k=5)
        except Exception as e:
            logger.warning("[query_knowledge_some_like] vector search failed: %s", e)
            return []
        if not vector_results:
            return []
        kid_to_score = {r["kid"]: r.get("score", 0.0) for r in vector_results}
        kids = [r["kid"] for r in vector_results]
        entities = get_knowledge_by_ids(kids)
        return [
            _entity_to_dict(e, similarity=kid_to_score.get(e.id))
            for e in entities
            if e.id in kid_to_score
        ]

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
        content: Optional[str] = None,
        source_type: Optional[str] = None,
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
        content_str = (str(content) if content is not None else "") or ""
        now_ms = int(time.time() * 1000)
        entity = create_knowledge(
            title=t,
            description=desc_str or None,
            content=content_str or None,
            source_type=st,
            ct=now_ms,
            ut=now_ms,
        )
        return _entity_to_dict(entity)

    def update_knowledge(
        self,
        entity_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        source_type: Optional[str] = None,
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
        if content is not None:
            c = str(content) if not isinstance(content, str) else content
            updates["content"] = c
        if source_type is not None:
            st = (str(source_type) if not isinstance(source_type, str) else source_type).strip() or "unknown"
            if len(st) > SOURCE_TYPE_MAX_LEN:
                raise ValueError(f"source_type must be at most {SOURCE_TYPE_MAX_LEN} characters")
            updates["source_type"] = st
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
