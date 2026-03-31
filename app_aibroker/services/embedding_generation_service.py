import logging
import time
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.services.llm_client_service import create_embedding
from app_aibroker.services.ai_model_param_specs_wire import (
    wire_param_children,
    wire_param_name,
    wire_param_type,
)
from app_aibroker.services.text_generation_service import (
    _apply_model_param_placeholders,
    _apply_spec_x_to_merged,
    _coerce_model_params,
    _flatten_ai_model_param_specs_for_coerce,
    _load_ai_model_param_specs_tree,
    _merge_model_param_defaults,
    _normalize_coerce_flat_type,
)
from common.utils.nested_typed_tree_util import wrap_object_array_dict_branches_as_single_element_lists
from common.consts.response_const import RET_AI_ERROR, RET_INVALID_PARAM

logger = logging.getLogger(__name__)

INVALID_DIMENSIONS_MSG = "dimensions must be a positive integer"

if TYPE_CHECKING:
    from app_aibroker.models.reg import Reg


def create_call_log(**kwargs):
    from app_aibroker.repos.call_log_repo import create_call_log as _impl

    return _impl(**kwargs)


def default_embedding_model():
    from app_aibroker.repos.provider_repo import default_embedding_model as _impl

    return _impl()


def get_model_by_id(model_id: int):
    from app_aibroker.repos.model_repo import get_model_by_id as _impl

    return _impl(model_id)


def get_provider_by_id(provider_id: int):
    from app_aibroker.repos.provider_repo import get_provider_by_id as _impl

    return _impl(provider_id)


def list_models_for_provider(provider_id: int):
    from app_aibroker.repos.model_repo import list_models_for_provider as _impl

    return _impl(provider_id)


def embed_text(
        reg: "Reg",
        payload: dict,
        model_api_kwargs: Optional[dict[str, Any]] = None,
) -> Tuple[dict, Optional[str], Optional[int]]:
    """
    Returns (result_dict, error_message, error_code).
    error_code is None on success; on failure use with resp_err(..., code=error_code).
    """
    raw_input = payload.get("input")
    if raw_input is None or not isinstance(raw_input, str) or not raw_input.strip():
        return {}, "input is required (non-empty string)", RET_AI_ERROR

    dimensions: Optional[int] = None
    raw_dim = payload.get("dimensions")
    if raw_dim is not None:
        if isinstance(raw_dim, bool):
            return {}, INVALID_DIMENSIONS_MSG, RET_INVALID_PARAM
        try:
            d = int(raw_dim)
            if d <= 0:
                return {}, INVALID_DIMENSIONS_MSG, RET_INVALID_PARAM
            dimensions = d
        except (TypeError, ValueError):
            return {}, INVALID_DIMENSIONS_MSG, RET_INVALID_PARAM

    model_id = payload.get("model_id")
    provider_id = payload.get("provider_id")

    extra = dict(model_api_kwargs or {})
    body_raw: dict[str, Any] = {**extra, "input": raw_input.strip()}
    if dimensions is not None:
        body_raw["dimensions"] = dimensions

    model = None
    if model_id:
        model = get_model_by_id(int(model_id))
        if not model or model.status != 1 or model.capability != ModelCapabilityEnum.EMBEDDING:
            return {}, "model not found, inactive, or not an embedding model", RET_AI_ERROR
        provider = get_provider_by_id(model.provider_id)
    elif provider_id:
        provider = get_provider_by_id(int(provider_id))
        if not provider or provider.status != 1:
            return {}, "provider not found or inactive", RET_AI_ERROR
        for m in list_models_for_provider(provider.id):
            if m.capability == ModelCapabilityEnum.EMBEDDING and m.status == 1:
                model = m
                break
        if not model:
            return {}, "no embedding model for provider", RET_AI_ERROR
    else:
        provider, model = default_embedding_model()
        if not provider or not model:
            return (
                {},
                f"no active embedding provider/model; add ai_model with capability={ModelCapabilityEnum.EMBEDDING}",
                RET_AI_ERROR,
            )

    specs = _flatten_ai_model_param_specs_for_coerce(
        _load_ai_model_param_specs_tree(model.param_specs)
    )
    if not specs:
        request_body: dict[str, Any] = {"input": body_raw["input"]}
        if dimensions is not None:
            request_body["dimensions"] = dimensions
    else:
        merged = _merge_model_param_defaults(body_raw, specs)
        _apply_spec_x_to_merged(merged, specs, "model", model.model_name)
        coerced, coerce_err = _coerce_model_params(merged, specs)
        if coerce_err:
            return {}, coerce_err, RET_INVALID_PARAM
        placeholder_err = _apply_model_param_placeholders(
            coerced, specs, extra, body_raw["input"], synthetic_key="input"
        )
        if placeholder_err:
            return {}, placeholder_err, RET_INVALID_PARAM
        wrap_object_array_dict_branches_as_single_element_lists(
            _load_ai_model_param_specs_tree(model.param_specs),
            coerced,
            get_local_name=wire_param_name,
            get_type_tag=wire_param_type,
            get_child_list=wire_param_children,
            normalize_type_tag=_normalize_coerce_flat_type,
        )
        request_body = coerced

    started = time.perf_counter()
    err_msg = None
    vec: Optional[List[float]] = None
    try:
        vec = create_embedding(provider, model, request_body)
    except Exception as exc:
        logger.exception("[aibroker] embedding failed")
        err_msg = str(exc)

    latency_ms = int((time.perf_counter() - started) * 1000)
    success = err_msg is None and vec is not None

    create_call_log(
        reg_id=reg.id,
        template_id=0,
        provider_id=provider.id,
        model_id=model.id,
        latency_ms=latency_ms,
        success=success,
        error_message=err_msg or "",
    )

    if not success:
        return {}, err_msg or "embedding failed", RET_AI_ERROR

    return (
        {
            "embedding": vec,
            "provider_id": provider.id,
            "model_id": model.id,
            "dimensions": len(vec),
            "latency_ms": latency_ms,
        },
        None,
        None,
    )
