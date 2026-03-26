import threading

from app_notice.enums import ChannelEnum
from app_notice.services.email_notice_service import EmailNoticeService
from app_notice.services.sms_notice_service import SmsNoticeService
from app_notice.repos import (
    create_notice_record,
    update_notice_record_status,
    get_reg_by_access_key,
)


def _send_record(record_id: int, channel: int, target: str, subject: str, content: str):
    provider = ""
    message = "ok"
    status = 0
    try:
        if channel == ChannelEnum.EMAIL.value:
            EmailNoticeService.send(subject=subject or "Notice", body=content, recipients=[target])
            provider = "django_email"
            status = 1
        elif channel == ChannelEnum.SMS.value:
            provider = "sms"
            status = 1 if SmsNoticeService.send(phone=target, content=content) else 0
            if status == 0:
                message = "sms send failed"
        else:
            message = "unsupported channel"
            status = 0
    except Exception as exc:
        message = str(exc)
        status = 0
    finally:
        update_notice_record_status(record_id=record_id, status=status, provider=provider, message=message)


def enqueue_notice_by_payload(payload: dict) -> dict:
    access_key = (payload.get("access_key") or "").strip()
    channel = int(payload.get("channel"))
    target = (payload.get("target") or "").strip()
    subject = (payload.get("subject") or "").strip()
    content = payload.get("content") or ""
    event_id = int(payload.get("event_id") or 0)
    if channel not in ChannelEnum.values():
        raise ValueError(f"channel must be one of {ChannelEnum.values()}")
    if not target or not content or event_id <= 0:
        raise ValueError("target, content and event_id are required")
    reg = get_reg_by_access_key(access_key)
    if not reg or reg.status != 1:
        raise ValueError("invalid access_key")

    record = create_notice_record(
        reg_id=reg.id,
        event_id=event_id,
        channel=channel,
        target=target,
        subject=subject,
        content=content,
        status=0,
        provider="",
        message="queued",
    )
    threading.Thread(
        target=_send_record,
        args=(record.id, channel, target, subject, content),
        daemon=True,
    ).start()
    return {"notice_id": record.id, "event_id": event_id, "queued": True}
