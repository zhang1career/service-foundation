import logging
from typing import TYPE_CHECKING, List, Optional

from common.apis.aigcbest_api import AigcBestAPI

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app_aibroker.models.ai_model import AiModel
    from app_aibroker.models.ai_provider import AiProvider


def create_embedding(
        provider: "AiProvider",
        model: "AiModel",
        input_text: str,
        dimensions: Optional[int] = None,
) -> List[float]:
    api = AigcBestAPI(
        model.model_name,
        base_url=provider.base_url,
        api_key=provider.api_key,
    )
    return api.embed(input_text, dimensions=dimensions)


def chat_completion(
        provider: "AiProvider",
        model: "AiModel",
        prompt: str,
        temperature: float = 0.7,
) -> Optional[str]:
    api = AigcBestAPI(
        model.model_name,
        base_url=provider.base_url,
        api_key=provider.api_key,
    )
    return api.chat(prompt, temperature=temperature)
