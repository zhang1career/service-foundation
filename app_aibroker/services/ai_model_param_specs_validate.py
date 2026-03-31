"""Validate ai_model.param_specs wire JSON before persistence."""

from __future__ import annotations

from typing import Optional

from app_aibroker.services.ai_model_param_specs_wire import (
    wire_param_children,
    wire_param_name,
    wire_param_type,
)
from common.enums.nested_type_enum import NestedParamType
from common.utils.nested_typed_tree_util import (
    DEFAULT_BRANCH_TAGS,
    try_parse_json_list,
    validate_typed_record_tree,
)


def validate_ai_model_param_specs_json(raw: str) -> Optional[str]:
    """Return an error message or ``None`` if *raw* is valid (including blank)."""
    nodes, err = try_parse_json_list(raw)
    if err:
        return f"param_specs {err}"
    if not nodes:
        return None
    return validate_typed_record_tree(
        nodes,
        get_local_name=wire_param_name,
        get_type_tag=wire_param_type,
        get_child_list=wire_param_children,
        allowed_type_tags=NestedParamType.all_tag_values(),
        branch_tags=DEFAULT_BRANCH_TAGS,
    )
