import logging
import time
from typing import TYPE_CHECKING, List, Optional, Tuple

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.services.llm_client_service import create_embedding
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

    started = time.perf_counter()
    err_msg = None
    vec: Optional[List[float]] = None
    try:
        vec = create_embedding(provider, model, raw_input.strip(), dimensions=dimensions)
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
