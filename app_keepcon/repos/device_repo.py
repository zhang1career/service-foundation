from __future__ import annotations

import re
import secrets
from typing import Optional

from django.db import transaction

from app_keepcon.enums.device_type_enum import KeepconDeviceType
from app_keepcon.models import KeepconDevice, KeepconMessage
from common.utils.date_util import get_now_timestamp_ms

_DB = "keepcon_rw"

_DEVICE_KEY_RE = re.compile(r"^[\w.-]{1,64}$")


def validate_device_key(device_key: str) -> str:
    key = (device_key or "").strip()
    if not _DEVICE_KEY_RE.match(key):
        raise ValueError("device_key must match [\\w.-]{1,64}")
    return key


def create_device(
    device_key: str,
    device_type: int | str = KeepconDeviceType.MOBILE,
    name: str = "",
    status: int = 1,
) -> KeepconDevice:
    key = validate_device_key(device_key)
    now_ms = get_now_timestamp_ms()
    secret = secrets.token_hex(32)
    dt = KeepconDeviceType.normalize(device_type)
    return KeepconDevice.objects.using(_DB).create(
        device_key=key,
        secret=secret,
        device_type=dt,
        name=(name or "")[:128],
        status=status,
        next_seq=0,
        last_seen_at=0,
        ct=now_ms,
        ut=now_ms,
    )


def list_devices() -> list[KeepconDevice]:
    return list(KeepconDevice.objects.using(_DB).all().order_by("-id"))


def get_device_by_id(device_row_id: int) -> Optional[KeepconDevice]:
    return KeepconDevice.objects.using(_DB).filter(id=device_row_id).first()


def get_device_by_key(device_key: str) -> Optional[KeepconDevice]:
    key = validate_device_key(device_key)
    return KeepconDevice.objects.using(_DB).filter(device_key=key).first()


def authenticate_device(device_key: str, secret: str) -> Optional[KeepconDevice]:
    key = validate_device_key(device_key)
    sec = (secret or "").strip()
    if not sec:
        return None
    dev = KeepconDevice.objects.using(_DB).filter(device_key=key, secret=sec, status=1).first()
    return dev


def update_device_last_seen(device_row_id: int) -> None:
    KeepconDevice.objects.using(_DB).filter(id=device_row_id).update(
        last_seen_at=get_now_timestamp_ms(),
        ut=get_now_timestamp_ms(),
    )


def update_device(
    device_row_id: int,
    name: str | None = None,
    device_type: int | str | None = None,
    status: int | None = None,
) -> Optional[KeepconDevice]:
    dev = get_device_by_id(device_row_id)
    if not dev:
        return None
    update_fields: list[str] = []
    if name is not None:
        dev.name = name[:128]
        update_fields.append("name")
    if device_type is not None:
        dev.device_type = KeepconDeviceType.normalize(device_type)
        update_fields.append("device_type")
    if status is not None:
        dev.status = status
        update_fields.append("status")
    if update_fields:
        dev.ut = get_now_timestamp_ms()
        update_fields.append("ut")
        dev.save(using=_DB, update_fields=update_fields)
    return dev


def delete_device(device_row_id: int) -> bool:
    deleted, _ = KeepconDevice.objects.using(_DB).filter(id=device_row_id).delete()
    return deleted > 0


def allocate_seq_and_create_message(
    device_row_id: int,
    payload_json: str,
    idem_key: str | None,
) -> tuple[KeepconDevice, KeepconMessage]:
    with transaction.atomic(using=_DB):
        dev = (
            KeepconDevice.objects.using(_DB)
            .select_for_update()
            .filter(id=device_row_id, status=1)
            .first()
        )
        if not dev:
            raise ValueError("device not found or disabled")
        if idem_key:
            existing = (
                KeepconMessage.objects.using(_DB)
                .filter(idem_key=idem_key.strip())
                .first()
            )
            if existing:
                return dev, existing
        next_seq = dev.next_seq + 1
        KeepconDevice.objects.using(_DB).filter(pk=dev.pk).update(
            next_seq=next_seq,
            ut=get_now_timestamp_ms(),
        )
        msg = KeepconMessage.objects.using(_DB).create(
            device_id=dev.id,
            seq=next_seq,
            payload=payload_json,
            status=KeepconMessage.MSG_PENDING,
            idem_key=idem_key.strip() if idem_key else None,
        )
        dev.next_seq = next_seq
        return dev, msg
