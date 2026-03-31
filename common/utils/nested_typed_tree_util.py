"""Utilities for trees of dict nodes with a type tag and optional child lists.

Used for nested field metadata (e.g. OpenAPI-style ``object`` / ``object_array``) and
helpers to coerce a single field from a flat type definition (``apply_field_coercion``).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from typing import Any, Optional

from common.enums.nested_type_enum import NestedParamType
from common.utils.dict_util import get_at_path, set_at_path

# Type tags that denote a branching node: non-empty *children* means recurse, not a leaf.
DEFAULT_BRANCH_TAGS = NestedParamType.branch_tag_values()

FieldCoerceFn = Callable[[str, Any, dict[str, Any]], tuple[Any, Optional[str]]]


def try_parse_json_list(raw: str | None) -> tuple[list[Any], Optional[str]]:
    """Parse *raw* as a JSON array; blank input → ``[]``. Return ``(items, error_message)``."""
    if raw is None or not str(raw).strip():
        return [], None
    try:
        arr = json.loads(raw)
    except json.JSONDecodeError:
        return [], "must be valid JSON"
    if not isinstance(arr, list):
        return [], "root must be a JSON array"
    return arr, None


def iter_typed_tree_leaves(
        items: list[Any],
        *,
        path_prefix: str = "",
        get_local_name: Callable[[dict[str, Any]], Optional[str]],
        get_type_tag: Callable[[dict[str, Any]], str],
        get_child_list: Callable[[dict[str, Any]], list[Any]],
        normalize_type_tag: Callable[[str], str],
        branch_tags: frozenset[str] = DEFAULT_BRANCH_TAGS,
) -> Iterator[tuple[dict[str, Any], str, str]]:
    """DFS: yield ``(node, dotted_path, normalized_type_tag)`` for leaf rows only.

    If the normalized tag is in *branch_tags* and *child_list* is non-empty, recurse
    without yielding the container as a leaf.
    """
    for x in items:
        if not isinstance(x, dict):
            continue
        name = get_local_name(x)
        if not name:
            continue
        full_path = f"{path_prefix}.{name}" if path_prefix else name
        tag = normalize_type_tag(get_type_tag(x))
        children = get_child_list(x)
        if tag in branch_tags and len(children) > 0:
            yield from iter_typed_tree_leaves(
                children,
                path_prefix=full_path,
                get_local_name=get_local_name,
                get_type_tag=get_type_tag,
                get_child_list=get_child_list,
                normalize_type_tag=normalize_type_tag,
                branch_tags=branch_tags,
            )
            continue
        yield x, full_path, tag


def walk_typed_tree_preorder(
        items: list[Any],
        *,
        depth: int = 0,
        get_local_name: Callable[[dict[str, Any]], Optional[str]],
        get_type_tag: Callable[[dict[str, Any]], str],
        get_child_list: Callable[[dict[str, Any]], list[Any]],
        normalize_type_tag: Callable[[str], str],
        visit: Callable[[dict[str, Any], int, str, list[Any]], None],
        branch_tags: frozenset[str] = DEFAULT_BRANCH_TAGS,
) -> None:
    """Preorder DFS: ``visit(node, depth, normalized_type_tag, children)`` then recurse."""
    for x in items:
        if not isinstance(x, dict):
            continue
        if not get_local_name(x):
            continue
        tag = normalize_type_tag(get_type_tag(x))
        children = get_child_list(x)
        visit(x, depth, tag, children)
        if tag in branch_tags and children:
            walk_typed_tree_preorder(
                children,
                depth=depth + 1,
                get_local_name=get_local_name,
                get_type_tag=get_type_tag,
                get_child_list=get_child_list,
                normalize_type_tag=normalize_type_tag,
                visit=visit,
                branch_tags=branch_tags,
            )


def validate_typed_record_tree(
        items: list[Any],
        *,
        get_local_name: Callable[[dict[str, Any]], Optional[str]],
        get_type_tag: Callable[[dict[str, Any]], str],
        get_child_list: Callable[[dict[str, Any]], list[Any]],
        allowed_type_tags: frozenset[str],
        branch_tags: frozenset[str] = DEFAULT_BRANCH_TAGS,
) -> Optional[str]:
    """Return an error string or ``None`` if every node is well-formed."""

    def walk(nodes: list[Any]) -> Optional[str]:
        for x in nodes:
            if not isinstance(x, dict):
                return "each entry must be an object"
            if not get_local_name(x):
                return "each entry needs a non-empty name"
            raw_tag = get_type_tag(x)
            tag = raw_tag.strip().upper() if raw_tag else ""
            if tag not in allowed_type_tags:
                return f"unknown type {raw_tag!r}"
            ch = get_child_list(x)
            if not isinstance(ch, list):
                return "children must be an array"
            if tag in branch_tags:
                if ch:
                    err = walk(ch)
                    if err:
                        return err
            elif ch:
                return "non-branching type must not have children"
        return None

    return walk(items)


def coerce_to_bool(_path: str, val: Any, _field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    if isinstance(val, bool):
        return val, None
    if isinstance(val, (int, float)) and val in (0, 1):
        return bool(int(val)), None
    if isinstance(val, str) and val.lower() in ("true", "false", "0", "1"):
        return val.lower() in ("true", "1"), None
    return None, "invalid bool"


def coerce_to_int_bounded(_path: str, val: Any, field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    bounds = field_def.get("range")
    if not isinstance(bounds, dict):
        bounds = {}
    i = int(val)
    mn = bounds.get("min")
    mx = bounds.get("max")
    if mn is not None and i < int(mn):
        return None, "below min"
    if mx is not None and i > int(mx):
        return None, "above max"
    return i, None


def coerce_to_float_bounded(_path: str, val: Any, field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    bounds = field_def.get("range")
    if not isinstance(bounds, dict):
        bounds = {}
    f_v = float(val)
    mn = bounds.get("min")
    mx = bounds.get("max")
    if mn is not None and f_v < float(mn):
        return None, "below min"
    if mx is not None and f_v > float(mx):
        return None, "above max"
    return f_v, None


def coerce_to_enum_choice(_path: str, val: Any, field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    bounds = field_def.get("range")
    if not isinstance(bounds, dict):
        bounds = {}
    choices = bounds.get("values")
    if not isinstance(choices, list) or not choices:
        return None, "invalid enum spec"
    for c in choices:
        if c == val or str(c) == str(val).strip():
            return c, None
    return None, "not in allowed values"


def coerce_to_json_list(_path: str, val: Any, _field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    if isinstance(val, list):
        return val, None
    parsed = json.loads(str(val))
    if not isinstance(parsed, list):
        return None, "must be a JSON array"
    return parsed, None


def coerce_to_object_list(path: str, val: Any, field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    coerced, err = coerce_to_json_list(path, val, field_def)
    if err:
        return None, err
    assert isinstance(coerced, list)
    for i, item in enumerate(coerced):
        if not isinstance(item, dict):
            return None, f"[{i}]: must be an object"
    return coerced, None


def coerce_to_object_like(_path: str, val: Any, _field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    if isinstance(val, (dict, list)):
        return val, None
    return json.loads(str(val)), None


def coerce_to_str_with_max_len(_path: str, val: Any, field_def: dict[str, Any]) -> tuple[Any, Optional[str]]:
    s = str(val)
    bounds = field_def.get("range")
    if isinstance(bounds, dict):
        mxlen = bounds.get("maxLength")
        if mxlen is not None and len(s) > int(mxlen):
            return None, "too long"
    return s, None


DEFAULT_FIELD_COERCE_HANDLERS_BY_TYPE: dict[str, FieldCoerceFn] = {
    NestedParamType.BOOL.value: coerce_to_bool,
    NestedParamType.INT.value: coerce_to_int_bounded,
    NestedParamType.FLOAT.value: coerce_to_float_bounded,
    NestedParamType.ENUM.value: coerce_to_enum_choice,
    NestedParamType.ARRAY.value: coerce_to_json_list,
    NestedParamType.OBJECT_ARRAY.value: coerce_to_object_list,
    NestedParamType.OBJECT.value: coerce_to_object_like,
}


def wrap_object_array_dict_branches_as_single_element_lists(
        items: list[Any],
        payload: dict[str, Any],
        *,
        get_local_name: Callable[[dict[str, Any]], Optional[str]],
        get_type_tag: Callable[[dict[str, Any]], str],
        get_child_list: Callable[[dict[str, Any]], list[Any]],
        normalize_type_tag: Callable[[str], str],
) -> None:
    """Fix dotted-path payloads for ``OBJECT_ARRAY`` branches that have child field nodes.

    Leaf paths like ``messages.role`` / ``messages.content`` are merged with
    :func:`common.utils.dict_util.set_at_path` into ``payload["messages"] = {…}``.
    For ``OBJECT_ARRAY`` that is the wrong JSON shape: the value must be a **list** of
    objects (often a single element). When the assembled value is a non-empty dict,
    replace it with ``[dict]``. Existing list values are left unchanged (e.g. client
    supplied a full JSON array for the branch).
    """
    for node in items:
        if not isinstance(node, dict):
            continue
        name = get_local_name(node)
        children = get_child_list(node)
        tag = normalize_type_tag(get_type_tag(node))
        if name and tag == NestedParamType.OBJECT_ARRAY.value and children:
            subtree, ok = get_at_path(payload, name)
            if ok and isinstance(subtree, dict) and subtree:
                set_at_path(payload, name, [subtree])
        if children:
            wrap_object_array_dict_branches_as_single_element_lists(
                children,
                payload,
                get_local_name=get_local_name,
                get_type_tag=get_type_tag,
                get_child_list=get_child_list,
                normalize_type_tag=normalize_type_tag,
            )


def apply_field_coercion(
        path: str,
        raw_value: Any,
        field_def: dict[str, Any],
        *,
        handlers_by_type_tag: Mapping[str, FieldCoerceFn] = DEFAULT_FIELD_COERCE_HANDLERS_BY_TYPE,
        default_handler: FieldCoerceFn = coerce_to_str_with_max_len,
        type_tag_key: str = "type",
) -> tuple[Any, Optional[str]]:
    """Dispatch *field_def*'s type tag; default map covers common JSON-ish primitive tags.

    *error* is either the handler's message or ``"invalid (...)"`` after conversion errors.
    """
    tag = field_def[type_tag_key]
    handler = handlers_by_type_tag.get(tag, default_handler)
    try:
        return handler(path, raw_value, field_def)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, f"invalid ({exc!s})"
