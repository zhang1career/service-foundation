import time

from app_aibroker.models import AiCallLog


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_call_log(
    reg_id: int,
    template_id: int,
    provider_id: int,
    model_id: int,
    latency_ms: int,
    success: bool,
    error_message: str = "",
) -> AiCallLog:
    return AiCallLog.objects.using("aibroker_rw").create(
        reg_id=reg_id,
        template_id=template_id,
        provider_id=provider_id,
        model_id=model_id,
        latency_ms=latency_ms,
        success=1 if success else 0,
        error_message=(error_message or "")[:512],
        ct=_now_ms(),
    )
