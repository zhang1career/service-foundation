"""
STUB: summary_mapping_repo - table x deleted in schema refactor.
All functions raise RuntimeError.
"""
from typing import List, Optional, Tuple

_NOT_AVAILABLE = "summary_mapping (table x) was deleted in schema refactor"


def get_mapping_by_knowledge_id(knowledge_id: int, app_id: Optional[int] = None):
    raise RuntimeError(_NOT_AVAILABLE)


def get_mapping_by_summary_id(summary_id: str, app_id: Optional[int] = None):
    raise RuntimeError(_NOT_AVAILABLE)


def list_mappings(
    app_id: Optional[int] = None,
    knowledge_ids: Optional[List[int]] = None,
    offset: int = 0,
    limit: int = 100,
) -> Tuple[List, int]:
    raise RuntimeError(_NOT_AVAILABLE)


def create_or_update_mapping(knowledge_id: int, app_id: int, summary_id: str):
    raise RuntimeError(_NOT_AVAILABLE)


def delete_mapping_by_knowledge_id(knowledge_id: int, app_id: Optional[int] = None) -> int:
    raise RuntimeError(_NOT_AVAILABLE)


def get_knowledge_ids_by_summary_ids(summary_ids: List[str], app_id: Optional[int] = None) -> List[int]:
    raise RuntimeError(_NOT_AVAILABLE)
