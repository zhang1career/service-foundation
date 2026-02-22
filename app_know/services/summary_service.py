"""
Summary service: generate and persist knowledge summaries; keep in sync with knowledge. Generated.
"""
import logging
from typing import Any, Dict, Optional

from app_know.repos import get_knowledge_by_id
from app_know.repos.summary_repo import (
    save_summary,
    get_summary as repo_get_summary,
    list_summaries as repo_list_summaries,
    delete_by_knowledge_id,
)
from app_know.services.summary_generator import generate_summary
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)


def _validate_knowledge_id(knowledge_id) -> None:
    if knowledge_id is None:
        raise ValueError("knowledge_id is required")
    if not isinstance(knowledge_id, int):
        try:
            knowledge_id = int(knowledge_id)
        except (TypeError, ValueError):
            raise ValueError("knowledge_id must be an integer")
    if knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")


def _validate_app_id(app_id: Optional[str]) -> str:
    app_id = (app_id or "").strip()
    if not app_id:
        raise ValueError("app_id is required and cannot be empty")
    return app_id


class SummaryService(Singleton):
    """Service for generating and persisting knowledge summaries (MongoDB)."""

    def generate_and_save(
        self,
        knowledge_id: int,
        app_id: str,
    ) -> Dict[str, Any]:
        """
        Load knowledge by id, generate summary from title/description, upsert to MongoDB.
        Raises ValueError if knowledge_id or app_id invalid, or knowledge not found.
        """
        _validate_knowledge_id(knowledge_id)
        app_id = _validate_app_id(app_id)
        entity = get_knowledge_by_id(knowledge_id)
        if not entity:
            raise ValueError(f"Knowledge entity with id {knowledge_id} not found")
        title = entity.title or ""
        description = entity.description or ""
        content = getattr(entity, "content", None) or entity.metadata or ""
        source_type = getattr(entity, "source_type", None) or ""
        summary_text = generate_summary(
            title=title,
            description=description,
            content=content,
            source_type=source_type,
        )
        return save_summary(
            knowledge_id=knowledge_id,
            summary=summary_text,
            app_id=app_id,
            source="title_description",
        )

    def get_summary(
        self,
        knowledge_id: int,
        app_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get one summary by knowledge_id, optionally filtered by app_id."""
        _validate_knowledge_id(knowledge_id)
        return repo_get_summary(knowledge_id=knowledge_id, app_id=app_id)

    def list_summaries(
        self,
        app_id: Optional[str] = None,
        knowledge_id: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        List summaries with optional filters. Returns dict with data, total_num, next_offset.
        offset and limit default to 0 and 100 when None. Raises ValueError for invalid types or range.
        """
        if offset is None:
            offset = 0
        if limit is None:
            limit = 100
        if not isinstance(offset, int):
            raise ValueError("offset must be an integer")
        if not isinstance(limit, int):
            raise ValueError("limit must be an integer")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit <= 0 or limit > LIMIT_LIST:
            raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
        items, total = repo_list_summaries(
            app_id=app_id,
            knowledge_id=knowledge_id,
            offset=offset,
            limit=limit,
        )
        next_offset = offset + len(items) if (offset + len(items)) < total else None
        return {
            "data": items,
            "total_num": total,
            "next_offset": next_offset,
        }

    def delete_summaries_for_knowledge(self, knowledge_id: int) -> int:
        """
        Delete all summaries for the given knowledge_id (sync on knowledge delete).
        Returns number of summaries deleted. Does not raise if knowledge_id invalid (returns 0).
        """
        if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
            return 0
        return delete_by_knowledge_id(knowledge_id=knowledge_id)
