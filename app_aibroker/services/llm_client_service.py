import logging
from typing import TYPE_CHECKING, Any, List, Optional

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from common.apis.aigc_api import AigcAPI

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app_aibroker.models.ai_model import AiModel
    from app_aibroker.models.ai_provider import AiProvider


def chat_completion(
        provider: "AiProvider",
        model: "AiModel",
        params: dict[str, Any],
) -> Optional[str]:
    api = AigcAPI(
        base_url=provider.base_url,
        api_key=provider.api_key,
    )
    op = ModelCapabilityEnum.aigc_invoke_op(model.capability)
    return api.invoke(provider.url_path, op, model.model_name, params)


def create_embedding(
        provider: "AiProvider",
        model: "AiModel",
        params: dict[str, Any],
) -> List[float]:
    api = AigcAPI(
        base_url=provider.base_url,
        api_key=provider.api_key,
    )
    op = ModelCapabilityEnum.aigc_invoke_op(model.capability)
    return api.invoke(provider.url_path, op, model.model_name, params)


def fetch_json(
        provider: "AiProvider",
        *,
        method: str,
        path: str,
) -> dict[str, Any]:
    api = AigcAPI(
        base_url=provider.base_url,
        api_key=provider.api_key,
    )
    return api.request_json(method=method, path=path)
