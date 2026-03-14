"""
STUB: component_mapping_repo - table y deleted in schema refactor.
Returns empty/default values to avoid crashes.
"""
from typing import Any, Dict, List, Optional

_TYPE_SUBJECT = 0
TYPE_OBJECT = 1
TYPE_SUBJECT = 0

_NOT_AVAILABLE = "component_mapping (table y) was deleted in schema refactor"


def create_mapping(
    knowledge_id: int,
    component_id: str,
    app_id: int,
    component_type: int = TYPE_SUBJECT,
) -> None:
    raise RuntimeError(_NOT_AVAILABLE)


def get_mappings_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[int] = None,
    component_type: Optional[int] = None,
) -> List[Dict[str, Any]]:
    return []  # Return empty to avoid breaking callers


def get_cids_by_knowledge_id(
    knowledge_id: int,
    app_id: Optional[int] = None,
    component_type: Optional[int] = None,
) -> List[str]:
    return []  # Return empty to avoid breaking callers
