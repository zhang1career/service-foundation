import logging
import time
from typing import List, Optional, Tuple

from app_aibroker.models import Reg
from app_aibroker.repos import (
    create_call_log,
    default_embedding_model,
    get_model_by_id,
    get_provider_by_id,
    list_models_for_provider,
)
from app_aibroker.services.llm_client_service import create_embedding

logger = logging.getLogger(__name__)


def embed_text(
    reg: Reg,
    payload: dict,
) -> Tuple[dict, Optional[str]]:
    """
    Returns (result_dict, error_message). result_dict has embedding, provider_id, model_id, latency_ms, dimensions.
    """
    raw_input = payload.get("input")
    if raw_input is None or not isinstance(raw_input, str) or not raw_input.strip():
        return {}, "input is required (non-empty string)"

    dimensions = payload.get("dimensions")
    if dimensions is not None:
        try:
            dimensions = int(dimensions)
            if dimensions <= 0:
                dimensions = None
        except (TypeError, ValueError):
            dimensions = None

    model_id = payload.get("model_id")
    provider_id = payload.get("provider_id")

    provider = None
    model = None
    if model_id:
        model = get_model_by_id(int(model_id))
        if not model or model.status != 1 or model.capability != 3:
            return {}, "model not found, inactive, or not an embedding model"
        provider = get_provider_by_id(model.provider_id)
    elif provider_id:
        provider = get_provider_by_id(int(provider_id))
        if not provider or provider.status != 1:
            return {}, "provider not found or inactive"
        for m in list_models_for_provider(provider.id):
            if m.capability == 3 and m.status == 1:
                model = m
                break
        if not model:
            return {}, "no embedding model for provider"
    else:
        provider, model = default_embedding_model()
        if not provider or not model:
            return {}, "no active embedding provider/model; add ai_model with capability=3"

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
        return {}, err_msg or "embedding failed"

    return {
        "embedding": vec,
        "provider_id": provider.id,
        "model_id": model.id,
        "dimensions": len(vec),
        "latency_ms": latency_ms,
    }, None
