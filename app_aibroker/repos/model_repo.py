import time
from typing import Optional

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.models import AiModel


def _ai_model_qs():
    return AiModel.objects.using("aibroker_rw")


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_model(
    provider_id: int,
    model_name: str,
    capability: int = ModelCapabilityEnum.CHAT,
    status: int = 1,
    param_specs: str = "",
) -> AiModel:
    now_ms = _now_ms()
    return _ai_model_qs().create(
        provider_id=provider_id,
        model_name=model_name,
        capability=capability,
        status=status,
        param_specs=param_specs or "",
        ct=now_ms,
        ut=now_ms,
    )


def list_models_for_provider(provider_id: int):
    return list(
        _ai_model_qs()
        .filter(provider_id=provider_id)
        .order_by("-id")
    )


def get_model_by_id(model_id: int) -> Optional[AiModel]:
    return _ai_model_qs().filter(id=model_id).first()


def update_model(
    model_id: int,
    model_name: str = None,
    capability: int = None,
    status: int = None,
    param_specs: str = None,
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
    if param_specs is not None:
        m.param_specs = param_specs or ""
        fields.append("param_specs")
    if fields:
        m.ut = _now_ms()
        fields.append("ut")
        m.save(using="aibroker_rw", update_fields=fields)
    return m


def delete_model(model_id: int) -> bool:
    deleted, _ = _ai_model_qs().filter(id=model_id).delete()
    return deleted > 0
