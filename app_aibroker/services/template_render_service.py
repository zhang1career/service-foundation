import json
import logging
import re
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from app_aibroker.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


def render_template_body(tpl: "PromptTemplate", variables: Optional[dict]) -> str:
    variables = variables or {}
    try:
        return tpl.body.format(**variables)
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
    Strong constraint: output_variables is a JSON array of {\"name\": \"...\"}.
    Parse JSON from model output and ensure each name exists as a key on the object.
    """
    if tpl.constraint_type != 1 or not tpl.output_variables:
        return model_text
    try:
        spec = json.loads(tpl.output_variables)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid output_variables on template: {exc}") from exc

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
