"""
Summary repository - knowledge_summaries collection disabled.

MongoDB Atlas knowledge_summaries is not used (account limits).
All functions return stubs: no persistence, no vector search.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

# Max query length for text search (kept for API validation)
QUERY_SEARCH_MAX_LEN = 2000

# Max stored summary length (chars)
SUMMARY_STORAGE_MAX_LEN = 50_000


def save_summary(
        knowledge_id: int,
        summary: str,
        app_id: int,
) -> Dict[str, Any]:
    """
    No-op: knowledge_summaries disabled. Validates inputs, returns stub.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if summary is None:
        raise ValueError("summary must be a string")
    if not isinstance(summary, str):
        raise ValueError("summary must be a string")
    if len(summary) > SUMMARY_STORAGE_MAX_LEN:
        raise ValueError(f"summary must not exceed {SUMMARY_STORAGE_MAX_LEN} characters")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    now_ms = int(time.time() * 1000)
    logger.info("[summary_repo] knowledge_summaries disabled, save_summary no-op for kid=%s", knowledge_id)
    return {"id": None, "kid": knowledge_id, "summary": summary, "app_id": app_id, "ct": now_ms, "ut": now_ms}


def get_summary(
        knowledge_id: int,
        app_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_summaries disabled. Always returns None.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return None
    return None


def list_summaries(
        app_id: Optional[str] = None,
        knowledge_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    No-op: knowledge_summaries disabled. Returns empty list.
    """
    if offset is None:
        raise ValueError("offset is required")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if limit is None:
        raise ValueError("limit is required")
    if not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    return [], 0


def delete_by_knowledge_id(knowledge_id: int) -> int:
    """
    No-op: knowledge_summaries disabled. Returns 0.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return 0
    return 0


def update_summary(
        knowledge_id: int,
        app_id: int,
        summary: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_summaries disabled. Returns None (not found).
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if summary is not None:
        if not isinstance(summary, str):
            raise ValueError("summary must be a string")
        if len(summary) > SUMMARY_STORAGE_MAX_LEN:
            raise ValueError(f"summary must not exceed {SUMMARY_STORAGE_MAX_LEN} characters")
    return None


def delete_summary(knowledge_id: int, app_id: int) -> bool:
    """
    No-op: knowledge_summaries disabled. Returns False (not found).
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    return False


def search_summaries_by_text(
        query: str,
        app_id: Optional[int] = None,
        limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    No-op: knowledge_summaries disabled. Returns empty list.
    """
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = (query or "").strip()
    if not q:
        raise ValueError("query cannot be empty")
    if len(q) > QUERY_SEARCH_MAX_LEN:
        raise ValueError(f"query must not exceed {QUERY_SEARCH_MAX_LEN} characters")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    return []


def ensure_summary_vector_index() -> bool:
    """
    No-op: knowledge_summaries disabled. Returns False.
    """
    logger.info("[summary_repo] knowledge_summaries disabled, ensure_summary_vector_index skipped")
    return False


def search_summaries_by_vector_filtered(
        query: str,
        app_id: Optional[int] = None,
        top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    No-op: knowledge_summaries disabled. Returns empty list.
    """
    return []


def search_summaries_by_vector(
        query: str,
        app_id: Optional[int] = None,
        limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    No-op: knowledge_summaries disabled. Returns empty list.
    """
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = (query or "").strip()
    if not q:
        raise ValueError("query cannot be empty")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    return []
