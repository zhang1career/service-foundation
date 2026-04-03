from app_user.enums.event_status_enum import EventStatusEnum
from app_user.models import Event
from common.utils.date_util import get_now_timestamp_ms


def create_event(
    biz_type: int,
    level: int,
    notice_channel: int,
    notice_target: str,
    payload_json: str,
) -> Event:
    now_ms = get_now_timestamp_ms()
    return Event.objects.using("user_rw").create(
        biz_type=biz_type,
        status=EventStatusEnum.INIT.value,
        level=level,
        notice_channel=notice_channel,
        notice_target=notice_target,
        payload_json=payload_json,
        ct=now_ms,
        ut=now_ms,
    )


def get_event_by_id(event_id: int):
    return Event.objects.using("user_rw").filter(id=event_id).first()


def cancel_pending_events_by_notice(biz_type: int, notice_channel: int, notice_target: str) -> None:
    now_ms = get_now_timestamp_ms()
    Event.objects.using("user_rw").filter(
        biz_type=int(biz_type),
        status=EventStatusEnum.PENDING_VERIFY.value,
        notice_channel=int(notice_channel),
        notice_target=notice_target or "",
    ).update(status=EventStatusEnum.FAILED.value, message="superseded", ut=now_ms)


def get_latest_pending_event_by_notice(biz_type: int, notice_channel: int, notice_target: str):
    return (
        Event.objects.using("user_rw")
        .filter(
            biz_type=int(biz_type),
            status=EventStatusEnum.PENDING_VERIFY.value,
            notice_channel=int(notice_channel),
            notice_target=notice_target or "",
        )
        .order_by("-id")
        .first()
    )


def update_event_after_code(event_id: int, verify_code_id: int, verify_ref_id: int) -> bool:
    event = get_event_by_id(event_id)
    if not event:
        return False
    event.verify_code_id = verify_code_id
    event.verify_ref_id = verify_ref_id
    event.status = EventStatusEnum.PENDING_VERIFY.value
    event.ut = get_now_timestamp_ms()
    event.save(using="user_rw", update_fields=["verify_code_id", "verify_ref_id", "status", "ut"])
    return True


def update_event_status(event_id: int, status: int, message: str = "") -> bool:
    event = get_event_by_id(event_id)
    if not event:
        return False
    event.status = status
    event.message = message
    event.ut = get_now_timestamp_ms()
    event.save(using="user_rw", update_fields=["status", "message", "ut"])
    return True


def list_events(offset: int, limit: int):
    query = Event.objects.using("user_rw").all()
    total = query.count()
    data = list(query.order_by("-ct")[offset:offset + limit])
    return data, total


def update_event_fields(
    event_id: int,
    *,
    biz_type=None,
    status=None,
    level=None,
    verify_code_id=None,
    verify_ref_id=None,
    notice_target=None,
    notice_channel=None,
    payload_json=None,
    message=None,
):
    event = get_event_by_id(event_id)
    if not event:
        return None
    update_fields = []
    if biz_type is not None:
        event.biz_type = int(biz_type)
        update_fields.append("biz_type")
    if status is not None:
        event.status = int(status)
        update_fields.append("status")
    if level is not None:
        event.level = int(level)
        update_fields.append("level")
    if verify_code_id is not None:
        event.verify_code_id = int(verify_code_id)
        update_fields.append("verify_code_id")
    if verify_ref_id is not None:
        event.verify_ref_id = int(verify_ref_id)
        update_fields.append("verify_ref_id")
    if notice_target is not None:
        event.notice_target = notice_target or ""
        update_fields.append("notice_target")
    if notice_channel is not None:
        event.notice_channel = int(notice_channel)
        update_fields.append("notice_channel")
    if payload_json is not None:
        event.payload_json = payload_json or "{}"
        update_fields.append("payload_json")
    if message is not None:
        event.message = message or ""
        update_fields.append("message")
    if update_fields:
        event.ut = get_now_timestamp_ms()
        update_fields.append("ut")
        event.save(using="user_rw", update_fields=update_fields)
    return event


def delete_event(event_id: int) -> bool:
    event = get_event_by_id(event_id)
    if not event:
        return False
    event.delete(using="user_rw")
    return True
