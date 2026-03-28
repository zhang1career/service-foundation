import time
from typing import Optional

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.models import AiModel


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_model(
    provider_id: int,
    model_name: str,
    capability: int = ModelCapabilityEnum.CHAT,
    status: int = 1,
) -> AiModel:
    now_ms = _now_ms()
    return AiModel.objects.using("aibroker_rw").create(
        provider_id=provider_id,
        model_name=model_name,
        capability=capability,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_models_for_provider(provider_id: int):
    return list(
        AiModel.objects.using("aibroker_rw")
        .filter(provider_id=provider_id)
        .order_by("-id")
    )


def get_model_by_id(model_id: int) -> Optional[AiModel]:
    return AiModel.objects.using("aibroker_rw").filter(id=model_id).first()


def update_model(
    model_id: int,
    model_name: str = None,
    capability: int = None,
    status: int = None,
) -> Optional[AiModel]:
    m = get_model_by_id(model_id)
    if not m:
        return None
    fields = []
    if model_name is not None:
        m.model_name = model_name
        fields.append("model_name")
    if capability is not None:
        m.capability = capability
        fields.append("capability")
    if status is not None:
        m.status = status
        fields.append("status")
    if fields:
        m.ut = _now_ms()
        fields.append("ut")
        m.save(using="aibroker_rw", update_fields=fields)
    return m


def delete_model(model_id: int) -> bool:
    deleted, _ = AiModel.objects.using("aibroker_rw").filter(id=model_id).delete()
    return deleted > 0
