import logging
import uuid
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

from common.consts.response_const import RET_OK

logger = logging.getLogger(__name__)


def aibroker_ask_and_answer(
    text: str,
    role: str,
    question: str,
    *,
    additional_question: str = "",
    temperature: float = 0.7,
    template_key: Optional[str] = None,
    variables: Optional[dict] = None,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
    base_url: Optional[str] = None,
    access_key: Optional[str] = None,
    timeout_sec: float = 120,
) -> str:
    """
    Build the same prompt as TextAI.ask_and_answer and send it via app_aibroker HTTP only.
    """
    from common.services.ai.text_ai import build_ask_and_answer_prompt

    prompt = build_ask_and_answer_prompt(
        text=text,
        role=role,
        question=question,
        additional_question=additional_question,
        is_debug=False,
    )
    return aibroker_text_generate(
        prompt,
        temperature=temperature,
        template_key=template_key,
        variables=variables,
        model_id=model_id,
        provider_id=provider_id,
        idempotency_key=idempotency_key,
        base_url=base_url,
        access_key=access_key,
        timeout_sec=timeout_sec,
    )


def aibroker_text_generate(
    prompt: str,
    *,
    temperature: float = 0.7,
    template_key: Optional[str] = None,
    variables: Optional[dict] = None,
    model_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
    base_url: Optional[str] = None,
    access_key: Optional[str] = None,
    timeout_sec: float = 120,
) -> str:
    """
    Call app_aibroker POST /v1/text/generate. Returns model text or raises on error.
    """
    root = (base_url or getattr(settings, "AIBROKER_SERVICE_URL", "") or "").rstrip("/")
    key = access_key or getattr(settings, "KNOW_AIBROKER_ACCESS_KEY", "") or ""
    if not root or not key:
        raise RuntimeError("AIBROKER_SERVICE_URL and KNOW_AIBROKER_ACCESS_KEY must be set")

    url = f"{root}/v1/text/generate"
    body: Dict[str, Any] = {"access_key": key, "prompt": prompt, "temperature": temperature}
    if template_key:
        body["template_key"] = template_key
        if variables is not None:
            body["variables"] = variables
    if model_id is not None:
        body["model_id"] = model_id
    if provider_id is not None:
        body["provider_id"] = provider_id

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Correlation-Id": str(uuid.uuid4()),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    resp = requests.post(url, json=body, headers=headers, timeout=timeout_sec)
    if resp.status_code != 200:
        raise RuntimeError(f"aibroker HTTP {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    if not data or data.get("errorCode") != RET_OK:
        raise RuntimeError(data.get("message") or "aibroker error")

    inner = data.get("data") or {}
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
    base_url: Optional[str] = None,
    access_key: Optional[str] = None,
    timeout_sec: float = 120,
) -> List[float]:
    """
    Call app_aibroker POST /v1/embeddings. Returns embedding vector (list of float).
    """
    root = (base_url or getattr(settings, "AIBROKER_SERVICE_URL", "") or "").rstrip("/")
    key = access_key or getattr(settings, "KNOW_AIBROKER_ACCESS_KEY", "") or ""
    if not root or not key:
        raise RuntimeError("AIBROKER_SERVICE_URL and KNOW_AIBROKER_ACCESS_KEY must be set")

    url = f"{root}/v1/embeddings"
    body: Dict[str, Any] = {"access_key": key, "input": input_text}
    if dimensions is not None:
        body["dimensions"] = dimensions
    if model_id is not None:
        body["model_id"] = model_id
    if provider_id is not None:
        body["provider_id"] = provider_id

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Correlation-Id": str(uuid.uuid4()),
    }

    resp = requests.post(url, json=body, headers=headers, timeout=timeout_sec)
    if resp.status_code != 200:
        raise RuntimeError(f"aibroker HTTP {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    if not data or data.get("errorCode") != RET_OK:
        raise RuntimeError(data.get("message") or "aibroker error")

    inner = data.get("data") or {}
    emb = inner.get("embedding")
    if not isinstance(emb, list) or not emb:
        raise RuntimeError("aibroker returned no embedding")
    return [float(x) for x in emb]
