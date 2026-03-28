import hashlib
import json
import logging
import time
from typing import TYPE_CHECKING, Optional, Tuple

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.services.llm_client_service import chat_completion
from app_aibroker.services.template_render_service import render_template_body, validate_output

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app_aibroker.models.reg import Reg


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
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalize_prompt_inputs(payload: dict) -> tuple[
    str, str, dict, float, Optional[int], Optional[int], Optional[int], Optional[str]]:
    prompt = (payload.get("prompt") or "").strip()
    template_key = (payload.get("template_key") or "").strip()
    variables = payload.get("variables") or {}
    if variables is not None and not isinstance(variables, dict):
        return "", "", {}, 0.0, None, None, None, "variables must be an object"

    temperature = float(payload.get("temperature", 0.7))
    model_id = payload.get("model_id")
    provider_id = payload.get("provider_id")

    tid_raw = payload.get("template_id")
    template_id_from_payload = None
    if tid_raw is not None and tid_raw != "":
        try:
            template_id_from_payload = int(tid_raw)
        except (TypeError, ValueError):
            return "", "", {}, 0.0, None, None, None, "template_id must be an integer"

    if template_key and template_id_from_payload is not None:
        return "", "", {}, 0.0, None, None, None, "use only one of template_key or template_id"
    return (
        prompt,
        template_key,
        variables,
        temperature,
        model_id,
        provider_id,
        template_id_from_payload,
        None,
    )


def _resolve_prompt_from_template(
        prompt: str,
        template_key: str,
        template_id_from_payload: Optional[int],
        variables: dict,
) -> tuple[str, int, Optional[object], Optional[str]]:
    template_id = 0
    tpl = None
    if template_key:
        tpl = get_template_by_key(template_key)
        if not tpl or tpl.status != 1:
            return "", 0, None, "template not found or inactive"
        template_id = tpl.id
        try:
            prompt = render_template_body(tpl, variables)
        except ValueError as exc:
            return "", 0, None, str(exc)
        return prompt, template_id, tpl, None

    if template_id_from_payload is not None:
        if template_id_from_payload <= 0:
            return "", 0, None, "template_id must be positive"
        tpl = get_template(template_id_from_payload)
        if not tpl or tpl.status != 1:
            return "", 0, None, "template not found or inactive"
        template_id = tpl.id
        try:
            prompt = render_template_body(tpl, variables)
        except ValueError as exc:
            return "", 0, None, str(exc)
        return prompt, template_id, tpl, None

    if not prompt:
        return "", 0, None, "prompt or template_key or template_id is required"
    return prompt, template_id, None, None


def _resolve_model_and_provider(model_id: Optional[int], provider_id: Optional[int]) -> tuple[
    Optional[object], Optional[object], Optional[str]]:
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


def _consume_idempotency_if_hit(reg_id: int, idempotency_key: Optional[str], payload: dict) -> tuple[
    Optional[dict], Optional[str]]:
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


def _generate_with_model(provider, model, prompt: str, temperature: float) -> tuple[Optional[str], Optional[str], int]:
    started = time.perf_counter()
    err_msg = None
    text_out = None
    try:
        text_out = chat_completion(provider, model, prompt, temperature=temperature)
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

    cached_result, idempotency_err = _consume_idempotency_if_hit(reg.id, idempotency_key, payload)
    if idempotency_err:
        return {}, idempotency_err
    if cached_result is not None:
        return cached_result, None

    provider, model, model_err = _resolve_model_and_provider(model_id, provider_id)
    if model_err:
        return {}, model_err

    text_out, err_msg, latency_ms = _generate_with_model(provider, model, prompt, temperature)
    success = err_msg is None and text_out is not None

    if success and tpl is not None:
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
