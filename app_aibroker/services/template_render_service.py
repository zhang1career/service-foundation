import json
import logging
import re
from typing import Any, Dict, Optional

from app_aibroker.models import PromptTemplate

logger = logging.getLogger(__name__)


def render_template_body(tpl: PromptTemplate, variables: Optional[dict]) -> str:
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


def validate_output(tpl: PromptTemplate, model_text: str) -> str:
    """
    Strong constraint: if output_schema_json has \"required\" array, parse JSON from model output
    and ensure keys exist. Returns normalized JSON string or original text for weak/empty schema.
    """
    if tpl.constraint_type != 1 or not tpl.output_schema_json:
        return model_text
    try:
        spec = json.loads(tpl.output_schema_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid output_schema_json on template: {exc}") from exc

    required = spec.get("required")
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
