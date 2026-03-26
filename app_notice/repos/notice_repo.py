import time

from app_notice.models import NoticeRecord


def _now_ms() -> int:
    return int(time.time() * 1000)


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
) -> NoticeRecord:
    now_ms = _now_ms()
    return NoticeRecord.objects.using("notice_rw").create(
        reg_id=reg_id,
        event_id=event_id,
        channel=channel,
        target=target,
        subject=subject,
        content=content,
        status=status,
        provider=provider,
        message=message,
        ct=now_ms,
        ut=now_ms,
    )


def update_notice_record_status(record_id: int, status: int, provider: str, message: str) -> bool:
    record = NoticeRecord.objects.using("notice_rw").filter(id=record_id).first()
    if not record:
        return False
    record.status = status
    record.provider = provider
    record.message = message
    record.ut = _now_ms()
    record.save(using="notice_rw", update_fields=["status", "provider", "message", "ut"])
    return True
