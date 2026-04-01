from common.utils.date_util import get_now_timestamp_ms
from common.utils.page_util import slice_window_for_page

from app_aibroker.models import AiCallLog

_BULK_DELETE_MAX = 500


def list_call_logs_page(page: int, page_size: int) -> tuple[list[AiCallLog], int, int]:
    """
    Paginated list ordered by ct desc, then id desc.
    Returns (rows, total_count, resolved_page).
    """
    ps = page_size if page_size >= 1 else 1
    qs = AiCallLog.objects.using("aibroker_rw").order_by("-ct", "-id")
    total = qs.count()
    offset, resolved, _ = slice_window_for_page(total, page, ps)
    rows = list(qs[offset : offset + ps])
    return rows, total, resolved


def get_call_log_by_id(log_id: int) -> AiCallLog | None:
    try:
        return AiCallLog.objects.using("aibroker_rw").get(pk=log_id)
    except AiCallLog.DoesNotExist:
        return None


def delete_call_log_by_id(log_id: int) -> int:
    """Returns number of deleted rows (0 or 1)."""
    _deleted_count, _ = AiCallLog.objects.using("aibroker_rw").filter(pk=log_id).delete()
    return int(_deleted_count)


def delete_call_logs_by_ids(log_ids: list[int]) -> int:
    """
    Delete call_log rows by primary keys. Deduplicates, ignores non-positive ids.
    Returns total number of deleted rows. Caps batch size to _BULK_DELETE_MAX.
    """
    uniq: list[int] = []
    seen: set[int] = set()
    for x in log_ids:
        try:
            v = int(x)
        except (TypeError, ValueError):
            continue
        if v <= 0 or v in seen:
            continue
        seen.add(v)
        uniq.append(v)
        if len(uniq) >= _BULK_DELETE_MAX:
            break
    if not uniq:
        return 0
    qs = AiCallLog.objects.using("aibroker_rw").filter(pk__in=uniq)
    total, _ = qs.delete()
    return int(total)


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
        ct=get_now_timestamp_ms(),
    )
