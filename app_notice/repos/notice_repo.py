from app_notice.models import NoticeRecord
from common.utils.date_util import get_now_timestamp_ms
from common.utils.page_util import slice_window_for_page


def create_notice_record(
    reg_id: int,
    event_id: int,
    channel: int,
    target: str,
    subject: str,
    content: str,
    status: int,
    provider: str,
    message: str,
    broker: int = 0,
) -> NoticeRecord:
    now_ms = get_now_timestamp_ms()
    return NoticeRecord.objects.using("notice_rw").create(
        reg_id=reg_id,
        event_id=event_id,
        channel=channel,
        target=target,
        subject=subject,
        content=content,
        broker=broker,
        status=status,
        provider=provider,
        message=message,
        ct=now_ms,
        ut=now_ms,
    )


def list_notice_records_page(page: int, page_size: int) -> tuple[list[NoticeRecord], int, int]:
    ps = page_size if page_size >= 1 else 1
    qs = NoticeRecord.objects.using("notice_rw").order_by("-ct", "-id")
    total = qs.count()
    offset, resolved, _ = slice_window_for_page(total, page, ps)
    rows = list(qs[offset : offset + ps])
    return rows, total, resolved


def get_notice_record_by_id(record_id: int) -> NoticeRecord | None:
    return NoticeRecord.objects.using("notice_rw").filter(id=record_id).first()


def delete_notice_record_by_id(record_id: int) -> int:
    deleted, _ = NoticeRecord.objects.using("notice_rw").filter(pk=record_id).delete()
    return int(deleted)


def update_notice_record_status(record_id: int, status: int, provider: str, message: str) -> bool:
    record = NoticeRecord.objects.using("notice_rw").filter(id=record_id).first()
    if not record:
        return False
    record.status = status
    record.provider = provider
    record.message = message
    record.ut = get_now_timestamp_ms()
    record.save(using="notice_rw", update_fields=["status", "provider", "message", "ut"])
    return True
