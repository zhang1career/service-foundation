from typing import Optional

from app_keepcon.models import KeepconMessage

_DB = "keepcon_rw"


def list_messages_for_device(
    device_row_id: int,
    limit: int = 100,
) -> list[KeepconMessage]:
    return list(
        KeepconMessage.objects.using(_DB)
        .filter(device_id=device_row_id)
        .order_by("-id")[:limit]
    )


def list_pending_since_seq(device_row_id: int, since_seq: int, limit: int = 50) -> list[KeepconMessage]:
    """Pending or delivered-but-unacked rows (excludes acked) for catch-up after reconnect."""
    return list(
        KeepconMessage.objects.using(_DB)
        .filter(device_id=device_row_id, seq__gt=since_seq)
        .exclude(status=KeepconMessage.MSG_ACKED)
        .order_by("seq")[:limit]
    )


def get_message_by_id_for_device(msg_id: int, device_row_id: int) -> Optional[KeepconMessage]:
    return (
        KeepconMessage.objects.using(_DB)
        .filter(id=msg_id, device_id=device_row_id)
        .first()
    )


def mark_delivered(msg_id: int, device_row_id: int) -> Optional[KeepconMessage]:
    msg = get_message_by_id_for_device(msg_id, device_row_id)
    if not msg or msg.status != KeepconMessage.MSG_PENDING:
        return msg
    msg.status = KeepconMessage.MSG_DELIVERED
    msg.save(using=_DB, update_fields=["status"])
    return msg


def mark_acked(msg_id: int, device_row_id: int) -> Optional[KeepconMessage]:
    msg = get_message_by_id_for_device(msg_id, device_row_id)
    if not msg:
        return None
    if msg.status == KeepconMessage.MSG_ACKED:
        return msg
    msg.status = KeepconMessage.MSG_ACKED
    msg.save(using=_DB, update_fields=["status"])
    return msg


def list_recent_messages(limit: int = 200) -> list[KeepconMessage]:
    return list(KeepconMessage.objects.using(_DB).select_related("device").order_by("-id")[:limit])
