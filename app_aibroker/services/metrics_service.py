import time

from django.db.models import Avg, Count, Q

from app_aibroker.models import AiCallLog


def _now_ms() -> int:
    return int(time.time() * 1000)


def summary_since(reg_id: int = None, window_ms: int = 86400000) -> dict:
    since = _now_ms() - window_ms
    qs = AiCallLog.objects.using("aibroker_rw").filter(ct__gte=since)
    if reg_id is not None:
        qs = qs.filter(reg_id=reg_id)
    agg = qs.aggregate(
        total=Count("id"),
        success=Count("id", filter=Q(success=1)),
        fail=Count("id", filter=Q(success=0)),
        avg_latency=Avg("latency_ms"),
    )
    total = agg["total"] or 0
    success = agg["success"] or 0
    rate = (success / total) if total else 0.0
    return {
        "window_ms": window_ms,
        "total_calls": total,
        "success_calls": success,
        "fail_calls": agg["fail"] or 0,
        "success_rate": round(rate, 4),
        "avg_latency_ms": round(float(agg["avg_latency"] or 0), 2),
    }
