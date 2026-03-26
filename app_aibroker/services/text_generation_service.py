import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from app_aibroker.models import Reg
from app_aibroker.repos import (
    create_call_log,
    default_chat_model,
    get_idempotency,
    get_latest_template,
    get_model_by_id,
    get_provider_by_id,
    get_template_by_key_version,
    list_models_for_provider,
    save_idempotency,
)
from app_aibroker.services.llm_client_service import chat_completion
from app_aibroker.services.template_render_service import render_template_body, validate_output

logger = logging.getLogger(__name__)


def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def generate_text(
    reg: Reg,
    payload: dict,
    idempotency_key: Optional[str] = None,
) -> Tuple[dict, Optional[str]]:
    """
    Returns (result_dict, error_message). result_dict has keys: text, provider_id, model_id, template_id, latency_ms
    """
    template_id = 0
    prompt = (payload.get("prompt") or "").strip()
    template_key = (payload.get("template_key") or "").strip()
    template_version = payload.get("template_version")
    variables = payload.get("variables") or {}
    if variables is not None and not isinstance(variables, dict):
        return {}, "variables must be an object"

    temperature = float(payload.get("temperature", 0.7))
    model_id = payload.get("model_id")
    provider_id = payload.get("provider_id")

    tpl = None
    if template_key:
        if template_version is not None:
            tpl = get_template_by_key_version(template_key, int(template_version))
        else:
            tpl = get_latest_template(template_key)
        if not tpl or tpl.status != 1:
            return {}, "template not found or inactive"
        template_id = tpl.id
        try:
            prompt = render_template_body(tpl, variables)
        except ValueError as exc:
            return {}, str(exc)
    elif not prompt:
        return {}, "prompt or template_key is required"

    if idempotency_key:
        existing = get_idempotency(reg.id, idempotency_key)
        if existing:
            if existing.req_hash != _hash_payload(payload):
                return {}, "idempotency key reused with different payload"
            try:
                return json.loads(existing.resp_json), None
            except json.JSONDecodeError:
                return {}, "cached idempotency response is corrupt"

    provider = None
    model = None
    if model_id:
        model = get_model_by_id(int(model_id))
        if not model or model.status != 1:
            return {}, "model not found or inactive"
        provider = get_provider_by_id(model.provider_id)
    elif provider_id:
        provider = get_provider_by_id(int(provider_id))
        if not provider or provider.status != 1:
            return {}, "provider not found or inactive"
        for m in list_models_for_provider(provider.id):
            if m.capability == 0 and m.status == 1:
                model = m
                break
        if not model:
            return {}, "no chat model for provider"
    else:
        provider, model = default_chat_model()
        if not provider or not model:
            return {}, "no active provider/model; configure ai_provider and ai_model"

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
