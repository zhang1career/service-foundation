from __future__ import annotations

from typing import Any

from django.conf import settings

from app_notice.enums import BrokerEnum, ChannelEnum
from app_notice.enums.broker_jiang_enum import BrokerJiangEnum
from app_notice.repos import (
    create_notice_record,
    get_notice_record_by_id,
    get_reg_by_access_key,
    update_notice_record_status,
)
from app_notice.services.channel_broker_map import channel_to_broker_channel_ids
from app_notice.services.email_notice_service import EmailNoticeService
from app_notice.services.sms_notice_service import SmsNoticeService
from common.consts.string_const import EMPTY_STRING
from common.services.thread.thread_pool import get_thread_pool_executor
from common.utils.type_util import parse_int_or_default

_NOTICE_SEND_POOL_NAME = "notice_send"


def enqueue_notice_by_payload(payload: dict) -> dict:
    access_key = (payload.get("access_key") or "").strip()
    channel = _parse_int_required(payload.get("channel"), "channel")
    target = (payload.get("target") or "").strip()
    subject = (payload.get("subject") or "").strip()
    content = payload.get("content") or ""
    try:
        event_id = parse_int_or_default(payload.get("event_id"), 0)
    except ValueError:
        raise ValueError("event_id must be an integer")
    if channel not in ChannelEnum.values():
        raise ValueError(f"channel must be one of {ChannelEnum.values()}")
    if not content or event_id <= 0:
        raise ValueError("content and event_id are required")

    broker_raw = payload.get("broker")
    broker: int
    if channel in (ChannelEnum.EMAIL.value, ChannelEnum.SMS.value):
        if broker_raw is not None and str(broker_raw).strip() != "":
            raise ValueError("broker must not be set for email/sms channels")
        broker = 0
        if not target:
            raise ValueError("target is required for email/sms")
    else:
        if broker_raw is None or str(broker_raw).strip() == "":
            raise ValueError("broker is required for this channel")
        broker = _parse_int_required(broker_raw, "broker")
        BrokerEnum.to_broker(broker)

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
        broker=broker,
    )
    get_thread_pool_executor(
        _NOTICE_SEND_POOL_NAME,
        max_workers=int(settings.NOTICE_SEND_THREAD_POOL_MAX_WORKERS),
    ).submit(_send_record, record.id, channel, target, subject, content, broker)
    return {"notice_id": record.id, "event_id": event_id, "queued": True}


def enqueue_resend_notice_record(record_id: int) -> dict:
    """Re-queue sending for an existing row (status must be 0)."""
    record = get_notice_record_by_id(record_id)
    if not record:
        raise ValueError("notice not found")
    if int(record.status) != 0:
        raise ValueError("仅未成功状态可发送")
    channel = int(record.channel)
    broker: int
    if channel in (ChannelEnum.EMAIL.value, ChannelEnum.SMS.value):
        broker = 0
    else:
        if int(record.broker) == 0:
            raise ValueError("该记录缺少 broker 信息，请使用「调用」页发送")
        broker = int(record.broker)
    update_notice_record_status(record_id=record_id, status=0, provider="", message="queued")
    get_thread_pool_executor(
        _NOTICE_SEND_POOL_NAME,
        max_workers=int(settings.NOTICE_SEND_THREAD_POOL_MAX_WORKERS),
    ).submit(
        _send_record,
        record.id,
        channel,
        (record.target or "").strip(),
        (record.subject or "").strip(),
        record.content or "",
        broker,
    )
    return {"notice_id": record.id, "queued": True}


def _parse_int_required(raw: Any, field: str) -> int:
    if raw is None:
        raise ValueError(f"{field} is required")
    if isinstance(raw, str) and not raw.strip():
        raise ValueError(f"{field} is required")
    try:
        return parse_int_or_default(raw, 0)
    except ValueError:
        raise ValueError(f"{field} must be an integer")


def _send_record(
        record_id: int,
        channel: int,
        target: str,
        subject: str,
        content: str,
        broker: int,
):
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
        elif broker != 0:
            provider, message, status = _send_record_by_broker(channel, target, subject, content, broker)
        else:
            message = "broker is required for this channel"
            status = 0
    except Exception as exc:
        message = str(exc)
        status = 0
    finally:
        update_notice_record_status(record_id=record_id, status=status, provider=provider, message=message)


def _send_record_by_broker(
        channel: int,
        target: str,
        subject: str,
        content: str,
        broker: int):
    broker_cls = BrokerEnum.to_broker(broker)
    if broker_cls is BrokerJiangEnum:
        m = channel_to_broker_channel_ids(BrokerJiangEnum)
        broker_ch = m.get(channel)
        if broker_ch is None:
            provider = EMPTY_STRING
            message = "channel not supported for this broker"
            status = 0
        else:
            ok, detail = BrokerJiangEnum.send_message(
                title=subject or "Notice",
                desp=content,
                channel=broker_ch,
            )
            provider = "broker_jiang"
            message = detail
            status = 1 if ok else 0
    else:
        provider = EMPTY_STRING
        message = f"unsupported broker class: {broker_cls}"
        status = 0
    return provider, message, status
