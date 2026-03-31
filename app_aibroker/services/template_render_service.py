import json
import logging
import re
from typing import TYPE_CHECKING, Any, Optional

from app_aibroker.consts.multimodal_const import (
    VARIABLE_KIND_TEXT,
    VARIABLE_KINDS_MEDIA,
)

if TYPE_CHECKING:
    from app_aibroker.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


def render_template_body(tpl: "PromptTemplate", variables: Optional[dict]) -> str:
    variables = variables or {}
    try:
        return tpl.body.format(**variables)
    except KeyError as exc:
        raise ValueError(f"template variable missing: {exc}") from exc


def parse_param_specs(raw: Optional[str]) -> list[dict[str, Any]]:
    """
    Parse param_specs JSON into ordered specs: {"name": str, "kind": str}.
    Unknown or missing kind defaults to text.
    """
    if raw is None or not isinstance(raw, str) or not raw.strip():
        return []
    try:
        arr = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(arr, list):
        return []
    out: list[dict[str, Any]] = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        n = item.get("name")
        if not isinstance(n, str) or not n.strip():
            continue
        kind_raw = item.get("kind")
        if kind_raw is None or (isinstance(kind_raw, str) and not kind_raw.strip()):
            kind = VARIABLE_KIND_TEXT
        elif isinstance(kind_raw, str):
            kind = kind_raw.strip().lower()
        else:
            kind = VARIABLE_KIND_TEXT
        out.append({"name": n.strip(), "kind": kind})
    return out


def text_variable_names_for_format(specs: list[dict[str, Any]]) -> Optional[set[str]]:
    """
    Names that participate in str.format. None means \"all keys in variables\" (legacy templates).
    """
    if not specs:
        return None
    names: set[str] = set()
    for s in specs:
        k = s.get("kind") or VARIABLE_KIND_TEXT
        if k in VARIABLE_KINDS_MEDIA:
            continue
        n = s.get("name")
        if isinstance(n, str) and n:
            names.add(n)
    return names


def render_template_body_with_specs(
        tpl: "PromptTemplate",
        variables: Optional[dict],
        specs: list[dict[str, Any]],
) -> str:
    """
    Like render_template_body, but omits media-kind variables from format() so file slots
    are not required in the JSON `variables` object.
    """
    variables = variables or {}
    limit = text_variable_names_for_format(specs)
    if limit is None:
        fmt_vars = variables
    else:
        fmt_vars = {k: variables[k] for k in limit if k in variables}
    try:
        return tpl.body.format(**fmt_vars)
    except KeyError as exc:
        raise ValueError(f"template variable missing: {exc}") from exc


def _extract_json_object(text: str) -> Any:
    s = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    return json.loads(s)


def _required_keys_from_name_list(spec: Any) -> list[str]:
    if not isinstance(spec, list):
        return []
    out: list[str] = []
    for item in spec:
        if isinstance(item, dict):
            n = item.get("name")
            if isinstance(n, str):
                n = n.strip()
                if n:
                    out.append(n)
    return out


def validate_output(tpl: "PromptTemplate", model_text: str) -> str:
    """
    Strong constraint: resp_specs is a JSON array of {\"name\": \"...\"}.
    Parse JSON from model output and ensure each name exists as a key on the object.
    """
    if tpl.constraint_type != 1 or not tpl.resp_specs:
        return model_text
    try:
        spec = json.loads(tpl.resp_specs)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid resp_specs on template: {exc}") from exc

    required = _required_keys_from_name_list(spec)
    if not required:
        return model_text

    try:
        obj = _extract_json_object(model_text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"model output is not valid JSON: {exc}") from exc

    if not isinstance(obj, dict):
        raise ValueError("model JSON output must be an object")
    for k in required:
        if k not in obj:
            raise ValueError(f"missing required output key: {k}")
    return json.dumps(obj, ensure_ascii=False)
