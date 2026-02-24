"""
Summary service: generate and persist knowledge summaries; keep in sync with knowledge. Generated.
"""
import logging
from typing import Any, Dict, Optional

from app_know.repos import get_knowledge_by_id
from app_know.repos.summary_mapping_repo import (
    create_or_update_mapping,
    delete_mapping_by_knowledge_id,
)
from app_know.repos.summary_repo import (
    delete_by_knowledge_id,
    delete_summary as repo_delete_summary,
    get_summary as repo_get_summary,
    list_summaries as repo_list_summaries,
    save_summary,
    update_summary as repo_update_summary,
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


def _validate_app_id(app_id, default=None) -> int:
    """Validate and return app_id as integer. 0 is valid (default). Raises ValueError if invalid."""
    from app_know.consts import APP_ID_DEFAULT
    dflt = default if default is not None else APP_ID_DEFAULT
    if app_id is None:
        return dflt
    if isinstance(app_id, int):
        if app_id < 0:
            raise ValueError("app_id must be a non-negative integer")
        return app_id
    if isinstance(app_id, str):
        s = app_id.strip()
        if not s:
            return dflt
        try:
            val = int(s)
            if val < 0:
                raise ValueError("app_id must be a non-negative integer")
            return val
        except ValueError:
            raise ValueError("app_id must be an integer")
    try:
        val = int(app_id)
        if val < 0:
            raise ValueError("app_id must be a non-negative integer")
        return val
    except (TypeError, ValueError):
        raise ValueError("app_id must be an integer")


class SummaryService(Singleton):
    """Service for generating and persisting knowledge summaries (MongoDB)."""

    def generate_and_save(
        self,
        knowledge_id: int,
        app_id,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Load knowledge by id, generate summary from title/description, upsert to MongoDB.
        Also creates/updates the MySQL mapping table for efficient querying.

        Args:
            knowledge_id: Knowledge entity ID
            app_id: Application ID (int, 0 for default)
            use_ai: If True, use AigcBestAPI for AI-powered generation

        Raises:
            ValueError: If knowledge_id or app_id invalid, or knowledge not found
        """
        _validate_knowledge_id(knowledge_id)
        app_id = _validate_app_id(app_id)
        logger.info(
            "[generate_and_save] Starting for knowledge_id=%s, app_id=%s, use_ai=%s",
            knowledge_id, app_id, use_ai
        )
        entity = get_knowledge_by_id(knowledge_id)
        if not entity:
            raise ValueError(f"Knowledge entity with id {knowledge_id} not found")
        title = entity.title or ""
        description = entity.description or ""
        content = getattr(entity, "content", None) or ""
        source_type = getattr(entity, "source_type", None) or ""
        logger.info(
            "[generate_and_save] Generating summary for title: %s",
            title[:50] if title else "(empty)"
        )
        summary_text = generate_summary(
            title=title,
            description=description,
            content=content,
            source_type=source_type,
            use_ai=use_ai,
        )
        logger.info(
            "[generate_and_save] Summary generated, length=%d, saving to Atlas",
            len(summary_text)
        )
        result = save_summary(
            knowledge_id=knowledge_id,
            summary=summary_text,
            app_id=app_id,
        )
        summary_id = result.get("id")
        if summary_id:
            try:
                create_or_update_mapping(
                    knowledge_id=knowledge_id,
                    summary_id=summary_id,
                    app_id=app_id,
                )
            except Exception as e:
                logger.warning(
                    "[generate_and_save] Failed to update mapping for knowledge_id=%s: %s",
                    knowledge_id, e
                )
        return result

    def get_summary(
        self,
        knowledge_id: int,
        app_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get one summary by knowledge_id, optionally filtered by app_id."""
        _validate_knowledge_id(knowledge_id)
        return repo_get_summary(knowledge_id=knowledge_id, app_id=app_id)

    def list_summaries(
        self,
        app_id: Optional[int] = None,
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

    def update_summary(
        self,
        knowledge_id: int,
        app_id,
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing summary. summary must be provided.
        Raises ValueError if not found or invalid input.
        """
        _validate_knowledge_id(knowledge_id)
        app_id = _validate_app_id(app_id)
        if summary is None:
            raise ValueError("summary must be provided")
        result = repo_update_summary(
            knowledge_id=knowledge_id,
            app_id=app_id,
            summary=summary,
        )
        if result is None:
            raise ValueError(f"Summary for knowledge id {knowledge_id} with app_id {app_id} not found")
        return result

    def delete_summary(
        self,
        knowledge_id: int,
        app_id,
    ) -> bool:
        """
        Delete a summary by (knowledge_id, app_id).
        Also deletes the MySQL mapping.
        Raises ValueError if not found.
        """
        _validate_knowledge_id(knowledge_id)
        app_id = _validate_app_id(app_id)
        deleted = repo_delete_summary(knowledge_id=knowledge_id, app_id=app_id)
        if not deleted:
            raise ValueError(f"Summary for knowledge id {knowledge_id} with app_id {app_id} not found")
        try:
            delete_mapping_by_knowledge_id(knowledge_id=knowledge_id, app_id=app_id)
        except Exception as e:
            logger.warning(
                "[delete_summary] Failed to delete mapping for knowledge_id=%s: %s",
                knowledge_id, e
            )
        return True

    def delete_summaries_for_knowledge(self, knowledge_id: int) -> int:
        """
        Delete all summaries for the given knowledge_id (sync on knowledge delete).
        Also deletes the MySQL mappings.
        Returns number of summaries deleted. Does not raise if knowledge_id invalid (returns 0).
        """
        if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
            return 0
        count = delete_by_knowledge_id(knowledge_id=knowledge_id)
        try:
            delete_mapping_by_knowledge_id(knowledge_id=knowledge_id)
        except Exception as e:
            logger.warning(
                "[delete_summaries_for_knowledge] Failed to delete mappings for knowledge_id=%s: %s",
                knowledge_id, e
            )
        return count
