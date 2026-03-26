import logging
from typing import List, Optional

from openai import OpenAI

from app_aibroker.models import AiModel, AiProvider

logger = logging.getLogger(__name__)


def create_embedding(
    provider: AiProvider,
    model: AiModel,
    input_text: str,
    dimensions: Optional[int] = None,
) -> List[float]:
    client = OpenAI(base_url=provider.base_url, api_key=provider.api_key)
    kwargs = {"model": model.model_name, "input": input_text}
    if dimensions is not None and dimensions > 0:
        kwargs["dimensions"] = dimensions
    response = client.embeddings.create(**kwargs)
    if not response or not response.data:
        raise RuntimeError("empty embedding response")
    return list(response.data[0].embedding)


def chat_completion(
    provider: AiProvider,
    model: AiModel,
    prompt: str,
    temperature: float = 0.7,
) -> Optional[str]:
    client = OpenAI(base_url=provider.base_url, api_key=provider.api_key)
    response = client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    if not response or not response.choices:
        return None
    return response.choices[0].message.content
