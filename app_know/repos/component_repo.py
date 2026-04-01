"""
Component repository - knowledge_components collection disabled.

MongoDB Atlas knowledge_components is not used (account limits).
All functions return stubs: no persistence, no vector search.
Synthetic cids (stub-{app_id}-{hash}) are used for Neo4j + MySQL mapping compatibility.
"""
import hashlib
import logging
from typing import Any, Dict, List, Optional

from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_components"
KEY_NAME_VEC = "name_vec"
NAME_VEC_DIM = 384


def _stub_cid(name: str, app_id: int) -> str:
    """Generate synthetic component id for stub mode."""
    h = hashlib.md5(name.encode()).hexdigest()[:12]
    return f"stub-{app_id}-{h}"


def find_similar_node(name: str, app_id: int, limit: int = 1) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_components disabled. Always returns None.
    """
    return None


def find_similar_nodes(name: str, app_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    No-op: knowledge_components disabled. Returns empty list.
    """
    return []


def find_node_by_name(name: str, app_id: int) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_components disabled. Returns None.
    """
    return None


def find_node_by_id(node_id: str) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_components disabled. Returns None.
    """
    return None


def get_or_create_node(
    name: str,
    app_id: int,
    node_type: str = "entity",
) -> Dict[str, Any]:
    """
    Stub: returns synthetic node without Atlas. cid is used for Neo4j + MySQL mapping.
    """
    if not name or not isinstance(name, str):
        raise ValueError("name is required and must be a string")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    name = name.strip()
    if not name:
        raise ValueError("name cannot be empty")
    cid = _stub_cid(name, app_id)
    now_ms = get_now_timestamp_ms()
    logger.info("[component_repo] knowledge_components disabled, get_or_create_node stub for name=%s", name[:50])
    return {
        "id": cid,
        "name": name,
        "app_id": app_id,
        "node_type": node_type,
        "ct": now_ms,
        "ut": now_ms,
        "is_new": True,
    }


def update_node(
    node_id: str,
    name: Optional[str] = None,
    node_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    No-op: knowledge_components disabled. Returns None.
    """
    if not node_id or not isinstance(node_id, str):
        raise ValueError("node_id is required and must be a string")
    return None


def delete_node(node_id: str) -> bool:
    """
    No-op: knowledge_components disabled. Returns False.
    """
    return False


def ensure_vector_index() -> bool:
    """
    No-op: knowledge_components disabled. Returns False.
    """
    logger.info("[component_repo] knowledge_components disabled, ensure_vector_index skipped")
    return False
