from __future__ import annotations

import uuid
from typing import Optional

from app_keepcon.models import KeepconReg
from common.utils.date_util import get_now_timestamp_ms

_DB = "keepcon_rw"


def create_reg(name: str, status: int = 0) -> KeepconReg:
    now_ms = get_now_timestamp_ms()
    return KeepconReg.objects.using(_DB).create(
        name=name,
        access_key=uuid.uuid4().hex,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_regs() -> list[KeepconReg]:
    return list(KeepconReg.objects.using(_DB).all().order_by("-id"))


def get_reg_by_id(reg_id: int) -> Optional[KeepconReg]:
    return KeepconReg.objects.using(_DB).filter(id=reg_id).first()


def get_reg_by_access_key_and_status(access_key: str, status: int) -> Optional[KeepconReg]:
    return (
        KeepconReg.objects.using(_DB)
        .filter(access_key=access_key, status=status)
        .first()
    )


def update_reg(
    reg_id: int,
    name: str | None = None,
    status: int | None = None,
) -> Optional[KeepconReg]:
    reg = get_reg_by_id(reg_id)
    if not reg:
        return None
    update_fields: list[str] = []
    if name is not None:
        reg.name = name
        update_fields.append("name")
    if status is not None:
        reg.status = status
        update_fields.append("status")
    if update_fields:
        reg.ut = get_now_timestamp_ms()
        update_fields.append("ut")
        reg.save(using=_DB, update_fields=update_fields)
    return reg


def delete_reg(reg_id: int) -> bool:
    deleted, _ = KeepconReg.objects.using(_DB).filter(id=reg_id).delete()
    return deleted > 0
