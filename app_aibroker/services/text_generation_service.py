import base64
import copy
import hashlib
import json
import logging
import time
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.models.ai_model import AiModel
from app_aibroker.models.ai_provider import AiProvider
from app_aibroker.models.prompt_template import PromptTemplate
from app_aibroker.services.ai_model_param_specs_wire import (
    wire_param_children,
    wire_param_description,
    wire_param_name,
    wire_param_placeholder,
    wire_param_range,
    wire_param_type,
)
from app_aibroker.services.llm_client_service import chat_completion
from app_aibroker.services.template_render_service import (
    parse_param_specs,
    render_template_body,
    render_template_body_with_specs,
    validate_output,
)
from common.enums.nested_type_enum import NestedParamType
from common.services.http import HttpCallError, HttpClientPool, request_sync
from common.utils.dict_util import get_at_path, set_at_path
from common.utils.nested_typed_tree_util import (
    apply_field_coercion,
    iter_typed_tree_leaves,
    walk_typed_tree_preorder,
    wrap_object_array_dict_branches_as_single_element_lists,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app_aibroker.models.reg import Reg


def _normalize_coerce_flat_type(t: str) -> str:
    return (t or "").strip().upper() or NestedParamType.STRING.value


def _normalize_detail_row_type(t: str) -> str:
    return (t or "").strip().upper() or NestedParamType.STRING.value


def create_call_log(**kwargs):
    from app_aibroker.repos.call_log_repo import create_call_log as _impl

    return _impl(**kwargs)


def default_chat_model():
    from app_aibroker.repos.provider_repo import default_chat_model as _impl

    return _impl()


def get_idempotency(reg_id: int, idempotency_key: str):
    from app_aibroker.repos.idempotency_repo import get_idempotency as _impl

    return _impl(reg_id, idempotency_key)


def get_latest_template(template_key: str):
    from app_aibroker.repos.template_repo import get_latest_template as _impl

    return _impl(template_key)


def get_model_by_id(model_id: int):
    from app_aibroker.repos.model_repo import get_model_by_id as _impl

    return _impl(model_id)


def get_provider_by_id(provider_id: int):
    from app_aibroker.repos.provider_repo import get_provider_by_id as _impl

    return _impl(provider_id)


def get_template(template_id: int):
    from app_aibroker.repos.template_repo import get_template as _impl

    return _impl(template_id)


def get_template_by_key(template_key: str):
    from app_aibroker.repos.template_repo import get_template_by_key as _impl

    return _impl(template_key)


def list_models_for_provider(provider_id: int):
    from app_aibroker.repos.model_repo import list_models_for_provider as _impl

    return _impl(provider_id)


def save_idempotency(reg_id: int, idempotency_key: str, payload: dict, result: dict):
    from app_aibroker.repos.idempotency_repo import save_idempotency as _impl

    return _impl(reg_id, idempotency_key, payload, result)


def _hash_payload(payload: dict) -> str:
    stable: dict[str, Any] = dict(payload)
    atts = stable.get("attachments")
    if isinstance(atts, list):
        digests: list[tuple[Any, Any]] = []
        for item in atts:
            if isinstance(item, dict):
                digests.append((item.get("sha256"), item.get("mime_type")))
        stable["attachments"] = sorted(digests)
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalize_attachments_list(raw: Any) -> tuple[list[dict[str, Any]], Optional[str]]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "attachments must be a list"
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            return [], "each attachment must be an object"
        url = item.get("url")
        mime = item.get("mime_type")
        sha = item.get("sha256")
        if not isinstance(url, str) or not url.strip():
            return [], "attachment url invalid"
        if not isinstance(mime, str) or not mime.strip():
            return [], "attachment mime_type invalid"
        if not isinstance(sha, str) or len(sha) != 64:
            return [], "attachment sha256 invalid"
        out.append(
            {
                "url": url.strip(),
                "mime_type": mime.strip().lower(),
                "sha256": sha,
                "object_key": item.get("object_key") or "",
                "original_name": item.get("original_name") or "",
            }
        )
    return out, None


def _attachment_summary_for_log(atts: list[dict[str, Any]]) -> str:
    if not atts:
        return ""
    kinds = [a.get("mime_type", "") for a in atts]
    keys = [str(a.get("object_key") or "")[:24] for a in atts]
    return f"n={len(atts)} mime={kinds} keys~={keys}"


def _load_ai_model_param_specs_tree(raw: Optional[str]) -> list[dict[str, Any]]:
    if raw is None or not str(raw).strip():
        return []
    try:
        arr = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return arr if isinstance(arr, list) else []


def _flatten_ai_model_param_specs_for_coerce(
        items: list[Any],
        prefix: str = "",
) -> list[dict[str, Any]]:
    """DFS: object rows with non-empty children contribute only nested leaves; bare object is one leaf."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node, full, t_s in iter_typed_tree_leaves(
            items,
            path_prefix=prefix,
            get_local_name=wire_param_name,
            get_type_tag=wire_param_type,
            get_child_list=wire_param_children,
            normalize_type_tag=_normalize_coerce_flat_type,
    ):
        if full in seen:
            continue
        seen.add(full)
        d_raw = node.get("default")
        def_s = d_raw.strip() if isinstance(d_raw, str) else ""
        ph_s = wire_param_placeholder(node)
        out.append(
            {
                "name": full,
                "type": t_s,
                "range": wire_param_range(node),
                "default": def_s,
                "x": ph_s,
            }
        )
    return out


def _ai_model_param_specs_detail_rows(raw: Optional[str]) -> list[dict[str, Any]]:
    """Depth-first rows with indent_level for console model detail."""
    rows: list[dict[str, Any]] = []

    def visit(node: dict[str, Any], depth: int, typ: str, _ch: list[Any]) -> None:
        n = wire_param_name(node)
        if not n:
            return
        desc = wire_param_description(node)
        rng = wire_param_range(node)
        rng_disp = ""
        if typ == NestedParamType.ENUM.value and isinstance(rng, dict):
            vals = rng.get("values")
            if isinstance(vals, list) and vals:
                rng_disp = ",".join(str(v) for v in vals)
        d_raw = node.get("default")
        default_disp = d_raw if isinstance(d_raw, str) else ""
        ph_disp = wire_param_placeholder(node)
        rows.append(
            {
                "name": n.strip(),
                "description": desc,
                "type": typ,
                "range_display": rng_disp,
                "default_display": default_disp,
                "placeholder_display": ph_disp,
                "indent_level": depth,
            }
        )

    walk_typed_tree_preorder(
        _load_ai_model_param_specs_tree(raw),
        depth=0,
        get_local_name=wire_param_name,
        get_type_tag=wire_param_type,
        get_child_list=wire_param_children,
        normalize_type_tag=_normalize_detail_row_type,
        visit=visit,
    )
    return rows


def _placeholder_name_to_value(
        model_params_raw: Any,
        resolved_payload: Union[str, list],
        *,
        synthetic_key: str = "content",
) -> dict[str, Any]:
    """Top-level ``model_params`` keys plus *synthetic_key* (e.g. rendered user message or ``input``)."""
    out: dict[str, Any] = {}
    if isinstance(model_params_raw, dict):
        for k, v in model_params_raw.items():
            if isinstance(k, str):
                out[k] = v
    out[synthetic_key] = resolved_payload
    return out


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    s = value.strip().lower()
    return s.startswith("http://") or s.startswith("https://")


def _download_base64_from_url(url: str) -> tuple[Optional[str], Optional[str]]:
    try:
        resp = request_sync(
            method="GET",
            url=url,
            pool_name=HttpClientPool.THIRD_PARTY,
            timeout_sec=30.0,
        )
    except HttpCallError as exc:
        return None, f"download media failed: {exc}"
    if resp.status_code >= 400:
        return None, f"download media failed: HTTP {resp.status_code}"
    raw = resp.content
    if not raw:
        return None, "download media failed: empty content"
    return base64.b64encode(raw).decode("ascii"), None


def _apply_spec_x_to_merged(
        merged: dict[str, Any],
        specs: list[dict[str, Any]],
        x: str,
        value: Any,
) -> None:
    for spec in specs:
        if spec.get("x") != x:
            continue
        path = spec.get("name")
        if isinstance(path, str) and path.strip():
            set_at_path(merged, path.strip(), value)


def _apply_model_param_placeholders(
        api_kwargs: dict[str, Any],
        specs: list[dict[str, Any]],
        model_params_raw: Any,
        resolved_payload: Union[str, list],
        *,
        synthetic_key: str = "content",
) -> Optional[str]:
    """If spec ``x`` equals a top-level ``model_params`` key name, copy that value to spec path."""
    sources = _placeholder_name_to_value(
        model_params_raw, resolved_payload, synthetic_key=synthetic_key
    )
    for spec in specs:
        ph = spec.get("x")
        if not isinstance(ph, str):
            continue
        key = ph.strip()
        if not key or key not in sources:
            continue
        path = spec.get("name")
        if not isinstance(path, str) or not path.strip():
            continue
        source_val = sources[key]
        # Keep OSS as source of truth; convert URL placeholders to base64 before upstream call.
        if _is_http_url(source_val):
            source_val, dl_err = _download_base64_from_url(str(source_val).strip())
            if dl_err:
                return f"model_params.{path}: {dl_err}"
        # Synthetic payload (e.g. content/input) may be rich objects; keep original shape.
        if key == synthetic_key:
            set_at_path(api_kwargs, path, source_val)
            continue
        coerced, err = apply_field_coercion(path, source_val, spec)
        if err:
            return f"model_params.{path}: {err}"
        set_at_path(api_kwargs, path, coerced)
    return None


def _merge_model_param_defaults(
        raw: dict[str, Any],
        specs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fill missing or empty leaf keys from spec.default (literal; coerced in _coerce_model_params)."""
    merged: dict[str, Any] = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    if not isinstance(merged, dict):
        merged = {}
    for spec in specs:
        name = spec.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        val, ok = get_at_path(merged, name)
        if ok and val is not None and val != "":
            continue
        def_raw = spec.get("default")
        if not isinstance(def_raw, str) or not def_raw.strip():
            continue
        set_at_path(merged, name, def_raw.strip())
    return merged


def _coerce_model_params(
        raw: Any,
        specs: list[dict[str, Any]],
) -> tuple[dict[str, Any], Optional[str]]:
    """Coerce by dotted leaf names; build nested dict for the HTTP API."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        return {}, "model_params must be an object"
    spec_by_name = {s["name"]: s for s in specs}
    out: dict[str, Any] = {}
    for path, field_def in spec_by_name.items():
        val, ok = get_at_path(raw, path)
        if not ok or val is None or val == "":
            continue
        coerced, err = apply_field_coercion(path, val, field_def)
        if err:
            return {}, f"model_params.{path}: {err}"
        set_at_path(out, path, coerced)
    return out, None


def _normalize_prompt_inputs(payload: dict) -> tuple[
    str,
    str,
    dict,
    float,
    Optional[int],
    Optional[int],
    Optional[int],
    list[dict[str, Any]],
    dict[str, Any],
    Optional[str],
]:
    prompt = (payload.get("prompt") or "").strip()
    template_key = (payload.get("template_key") or "").strip()
    variables = payload.get("variables") or {}
    if variables is not None and not isinstance(variables, dict):
        return "", "", {}, 0.0, None, None, None, [], {}, "variables must be an object"

    model_params_raw = payload.get("model_params")
    if model_params_raw is not None and not isinstance(model_params_raw, dict):
        return "", "", {}, 0.0, None, None, None, [], {}, "model_params must be an object"
    if model_params_raw is None:
        model_params_raw = {}

    attachments, att_err = _normalize_attachments_list(payload.get("attachments"))
    if att_err:
        return "", "", {}, 0.0, None, None, None, [], {}, att_err

    temperature = float(payload.get("temperature", 0.7))
    model_id = payload.get("model_id")
    provider_id = payload.get("provider_id")

    tid_raw = payload.get("template_id")
    template_id_from_payload = None
    if tid_raw is not None and tid_raw != "":
        try:
            template_id_from_payload = int(tid_raw)
        except (TypeError, ValueError):
            return "", "", {}, 0.0, None, None, None, [], {}, "template_id must be an integer"

    if template_key and template_id_from_payload is not None:
        return "", "", {}, 0.0, None, None, None, [], {}, "use only one of template_key or template_id"
    return (
        prompt,
        template_key,
        variables,
        temperature,
        model_id,
        provider_id,
        template_id_from_payload,
        attachments,
        model_params_raw,
        None,
    )


def _resolve_prompt_from_template(
        prompt: str,
        template_key: str,
        template_id_from_payload: Optional[int],
        variables: dict,
) -> tuple[str, int, Optional[PromptTemplate], Optional[str]]:
    template_id = 0
    tpl = None
    if template_key:
        tpl = get_template_by_key(template_key)
        if not tpl or tpl.status != 1:
            return "", 0, None, "template not found or inactive"
        template_id = tpl.id
        prompt, render_err = _render_prompt_by_template(tpl, variables)
        if render_err:
            return "", 0, None, render_err
        return prompt, template_id, tpl, None

    if template_id_from_payload is not None:
        if template_id_from_payload <= 0:
            return "", 0, None, "template_id must be positive"
        tpl = get_template(template_id_from_payload)
        if not tpl or tpl.status != 1:
            return "", 0, None, "template not found or inactive"
        template_id = tpl.id
        prompt, render_err = _render_prompt_by_template(tpl, variables)
        if render_err:
            return "", 0, None, render_err
        return prompt, template_id, tpl, None

    if not prompt:
        return "", 0, None, None
    return prompt, template_id, None, None


def _render_prompt_by_template(tpl_obj: PromptTemplate, variables: dict) -> tuple[str, Optional[str]]:
    try:
        specs = parse_param_specs(getattr(tpl_obj, "param_specs", None))
        if specs:
            return render_template_body_with_specs(tpl_obj, variables, specs), None
        return render_template_body(tpl_obj, variables), None
    except ValueError as exc:
        return "", str(exc)


def _resolve_model_and_provider(model_id: Optional[int],
                                provider_id: Optional[int]) -> tuple[Optional[AiProvider],
                                                                     Optional[AiModel],
                                                                     Optional[str]]:
    if model_id:
        model = get_model_by_id(int(model_id))
        if not model or model.status != 1:
            return None, None, "model not found or inactive"
        provider = get_provider_by_id(model.provider_id)
        return provider, model, None

    if provider_id:
        provider = get_provider_by_id(int(provider_id))
        if not provider or provider.status != 1:
            return None, None, "provider not found or inactive"
        model = None
        for m in list_models_for_provider(provider.id):
            if m.capability == ModelCapabilityEnum.CHAT and m.status == 1:
                model = m
                break
        if not model:
            return None, None, "no chat model for provider"
        return provider, model, None

    provider, model = default_chat_model()
    if not provider or not model:
        return None, None, "no active provider/model; configure ai_provider and ai_model"
    return provider, model, None


def _consume_idempotency_if_hit(reg_id: int,
                                idempotency_key: Optional[str],
                                payload: dict) -> tuple[Optional[dict], Optional[str]]:
    if not idempotency_key:
        return None, None
    existing = get_idempotency(reg_id, idempotency_key)
    if not existing:
        return None, None
    if existing.req_hash != _hash_payload(payload):
        return None, "idempotency key reused with different payload"
    try:
        return json.loads(existing.resp_json), None
    except json.JSONDecodeError:
        return None, "cached idempotency response is corrupt"


def _build_user_message_content(prompt: str,
                                attachments: list[dict[str, Any]]) -> Union[str, list[dict[str, Any]]]:
    if not attachments:
        return prompt
    parts: list[dict[str, Any]] = []
    p = (prompt or "").strip()
    if p:
        parts.append({"type": "text", "text": p})
    for att in attachments:
        mime = (att.get("mime_type") or "").lower()
        url = (att.get("url") or "").strip()
        if not url:
            continue
        if mime.startswith("image/"):
            parts.append({"type": "image_url", "image_url": {"url": url}})
        else:
            parts.append(
                {
                    "type": "text",
                    "text": f"[Attachment {mime or 'unknown'}]\n{url}",
                }
            )
    if not parts:
        parts.append({"type": "text", "text": ""})
    return parts


def _generate_with_model(provider,
                         model,
                         request_params: dict[str, Any]) -> tuple[Optional[str],
                                                                  Optional[str],
                                                                  int]:
    started = time.perf_counter()
    err_msg = None
    text_out = None
    try:
        text_out = chat_completion(provider, model, dict(request_params))
        if text_out is None:
            err_msg = "empty model response"
    except Exception as exc:
        logger.exception("[aibroker] chat completion failed")
        err_msg = str(exc)
    latency_ms = int((time.perf_counter() - started) * 1000)
    return text_out, err_msg, latency_ms


def generate_text(
        reg: "Reg",
        payload: dict,
        idempotency_key: Optional[str] = None,
) -> Tuple[dict, Optional[str]]:
    """
    Returns (result_dict, error_message). result_dict has keys: text, provider_id, model_id, template_id, latency_ms
    """
    (
        prompt,
        template_key,
        variables,
        temperature,
        model_id,
        provider_id,
        template_id_from_payload,
        attachments,
        model_params_raw,
        normalize_err,
    ) = _normalize_prompt_inputs(payload)
    if normalize_err:
        return {}, normalize_err

    prompt, template_id, tpl, template_err = _resolve_prompt_from_template(
        prompt,
        template_key,
        template_id_from_payload,
        variables,
    )
    if template_err:
        return {}, template_err

    if not (prompt or "").strip() and not attachments:
        return {}, "prompt (or template) or attachments required"

    att_summary = _attachment_summary_for_log(attachments)
    if att_summary:
        logger.info("[aibroker] multimodal request %s", att_summary)

    cached_result, idempotency_err = _consume_idempotency_if_hit(reg.id, idempotency_key, payload)
    if idempotency_err:
        return {}, idempotency_err
    if cached_result is not None:
        return cached_result, None

    provider, model, model_err = _resolve_model_and_provider(model_id, provider_id)
    if model_err:
        return {}, model_err

    user_content = _build_user_message_content(prompt, attachments)
    specs = _flatten_ai_model_param_specs_for_coerce(
        _load_ai_model_param_specs_tree(model.param_specs)
    )
    if not specs:
        request_body: dict[str, Any] = {
            "messages": [{"role": "user", "content": user_content}],
            "temperature": temperature,
        }
    else:
        merged_params = _merge_model_param_defaults(model_params_raw, specs)
        _apply_spec_x_to_merged(merged_params, specs, "model", model.model_name)
        coerced_params, coerce_err = _coerce_model_params(merged_params, specs)
        if coerce_err:
            return {}, coerce_err
        placeholder_err = _apply_model_param_placeholders(
            coerced_params, specs, model_params_raw, user_content
        )
        if placeholder_err:
            return {}, placeholder_err
        wrap_object_array_dict_branches_as_single_element_lists(
            _load_ai_model_param_specs_tree(model.param_specs),
            coerced_params,
            get_local_name=wire_param_name,
            get_type_tag=wire_param_type,
            get_child_list=wire_param_children,
            normalize_type_tag=_normalize_coerce_flat_type,
        )
        if "temperature" not in coerced_params:
            coerced_params["temperature"] = temperature
        request_body = coerced_params

    text_out, err_msg, latency_ms = _generate_with_model(
        provider,
        model,
        request_body,
    )
    success = err_msg is None and text_out is not None

    if success and tpl is not None and isinstance(text_out, str):
        try:
            text_out = validate_output(tpl, text_out)
        except ValueError as exc:
            success = False
            err_msg = str(exc)

    create_call_log(
        reg_id=reg.id,
        template_id=template_id,
        provider_id=provider.id,
        model_id=model.id,
        latency_ms=latency_ms,
        success=success,
        error_message=err_msg or "",
    )

    if not success:
        logger.warning(
            "[aibroker] generate_text failed reg_id=%s template_id=%s model_id=%s: %s",
            reg.id,
            template_id,
            model.id,
            err_msg or "generation failed",
        )
        return {}, err_msg or "generation failed"

    result = {
        "text": text_out,
        "provider_id": provider.id,
        "model_id": model.id,
        "template_id": template_id,
        "latency_ms": latency_ms,
    }
    if idempotency_key:
        save_idempotency(reg.id, idempotency_key, payload, result)
    return result, None
