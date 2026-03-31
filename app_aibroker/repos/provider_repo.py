import time
from typing import Optional

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.models import AiProvider
from app_aibroker.repos.model_repo import _ai_model_qs
from common.utils.http_util import normalize_http_path


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_provider(
    name: str,
    base_url: str,
    api_key: str,
    url_path: str,
    status: int = 1,
) -> AiProvider:
    now_ms = _now_ms()
    path = normalize_http_path(url_path)
    return AiProvider.objects.using("aibroker_rw").create(
        name=name,
        base_url=base_url.rstrip("/"),
        url_path=path,
        api_key=api_key,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_providers():
    return list(AiProvider.objects.using("aibroker_rw").all().order_by("-id"))


def get_provider_by_id(provider_id: int) -> Optional[AiProvider]:
    return AiProvider.objects.using("aibroker_rw").filter(id=provider_id).first()


def update_provider(
    provider_id: int,
    name: str = None,
    base_url: str = None,
    url_path: str | None = None,
    api_key: str = None,
    status: int = None,
) -> Optional[AiProvider]:
    p = get_provider_by_id(provider_id)
    if not p:
        return None
    fields = []
    if name is not None:
        p.name = name
        fields.append("name")
    if base_url is not None:
        p.base_url = base_url.rstrip("/")
        fields.append("base_url")
    if url_path is not None:
        p.url_path = normalize_http_path(url_path)
        fields.append("url_path")
    if api_key is not None:
        p.api_key = api_key
        fields.append("api_key")
    if status is not None:
        p.status = status
        fields.append("status")
    if fields:
        p.ut = _now_ms()
        fields.append("ut")
        p.save(using="aibroker_rw", update_fields=fields)
    return p


def delete_provider(provider_id: int) -> bool:
    _ai_model_qs().filter(provider_id=provider_id).delete()
    deleted, _ = AiProvider.objects.using("aibroker_rw").filter(id=provider_id).delete()
    return deleted > 0


def default_chat_model():
    """First active chat model with active provider."""
    for m in _ai_model_qs().filter(
        capability=ModelCapabilityEnum.CHAT, status=1
    ).order_by("id"):
        p = get_provider_by_id(m.provider_id)
        if p and p.status == 1:
            return p, m
    return None, None


def default_embedding_model():
    """First active embedding model with active provider."""
    for m in _ai_model_qs().filter(
        capability=ModelCapabilityEnum.EMBEDDING, status=1
    ).order_by("id"):
        p = get_provider_by_id(m.provider_id)
        if p and p.status == 1:
            return p, m
    return None, None
