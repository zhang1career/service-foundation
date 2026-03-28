"""
HTTP client for app_aibroker's public REST API.

Callers in other Django apps should import from here. Domain fields (template_id,
template_key, embedding payload shape, etc.) and HTTP transport live in this app
(see ``app_aibroker.http_transport``), not in ``common``.
"""
from typing import Any, Dict, List, Optional

from django.conf import settings

from app_aibroker.http_transport import aibroker_http_post, aibroker_http_post_embeddings


def aibroker_ask_and_answer_with_template(
    text: str,
    role: str,
    question: str,
    *,
    template_id: int,
    additional_question: str = "",
    temperature: float = 0.7,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> str:
    if template_id <= 0:
        raise RuntimeError("ask-and-answer template id must be a positive integer")

    return aibroker_text_generate(
        "",
        temperature=temperature,
        template_id=template_id,
        variables={
            "text": text,
            "role": role,
            "question": question,
            "additional_question": additional_question,
        },
        model_id=model_id,
        provider_id=provider_id,
        idempotency_key=idempotency_key,
    )


def aibroker_ask_and_answer(
    text: str,
    role: str,
    question: str,
    *,
    additional_question: str = "",
    temperature: float = 0.7,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> str:
    prompt_tpl_id = int(getattr(settings, "PROMPT_TEMPLATE_ID_ASK_AND_ANSWER", 0))
    if prompt_tpl_id <= 0:
        raise RuntimeError(
            "ask-and-answer template id is required; set PROMPT_TEMPLATE_ID_ASK_AND_ANSWER"
        )
    return aibroker_ask_and_answer_with_template(
        text,
        role,
        question,
        template_id=prompt_tpl_id,
        additional_question=additional_question,
        temperature=temperature,
        model_id=model_id,
        provider_id=provider_id,
        idempotency_key=idempotency_key,
    )


def aibroker_text_generate(
    prompt: str,
    *,
    temperature: float = 0.7,
    template_key: Optional[str] = None,
    template_id: Optional[int] = None,
    variables: Optional[dict] = None,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> str:
    if template_id is not None and template_key:
        raise RuntimeError("template_id and template_key are mutually exclusive")

    body: Dict[str, Any] = {"temperature": temperature}
    if template_id is not None:
        body["template_id"] = int(template_id)
        body["prompt"] = prompt or ""
        if variables is not None:
            body["variables"] = variables
    elif template_key:
        body["template_key"] = template_key
        body["prompt"] = prompt
        if variables is not None:
            body["variables"] = variables
    else:
        body["prompt"] = prompt
    if model_id is not None:
        body["model_id"] = model_id
    if provider_id is not None:
        body["provider_id"] = provider_id

    inner = aibroker_http_post(body, idempotency_key=idempotency_key)
    text = inner.get("text")
    if text is None:
        raise RuntimeError("aibroker returned no text")
    return str(text).strip()


def aibroker_embed(
    input_text: str,
    *,
    dimensions: Optional[int] = None,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
) -> List[float]:
    body: Dict[str, Any] = {"input": input_text}
    if dimensions is not None:
        body["dimensions"] = dimensions
    if model_id is not None:
        body["model_id"] = model_id
    if provider_id is not None:
        body["provider_id"] = provider_id

    inner = aibroker_http_post_embeddings(body)
    emb = inner.get("embedding")
    if not isinstance(emb, list) or not emb:
        raise RuntimeError("aibroker returned no embedding")
    return [float(x) for x in emb]
