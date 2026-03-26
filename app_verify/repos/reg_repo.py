import time
import uuid
from typing import Optional

from app_verify.models import Reg


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_reg(name: str, status: int = 0) -> Reg:
    now_ms = _now_ms()
    return Reg.objects.using("verify_rw").create(
        name=name,
        access_key=uuid.uuid4().hex,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_regs():
    return list(Reg.objects.using("verify_rw").all().order_by("-id"))


def get_reg_by_id(reg_id: int) -> Optional[Reg]:
    return Reg.objects.using("verify_rw").filter(id=reg_id).first()


def get_reg_by_access_key(access_key: str) -> Optional[Reg]:
    return Reg.objects.using("verify_rw").filter(access_key=access_key).first()


def update_reg(reg_id: int, name: str = None, status: int = None) -> Optional[Reg]:
    reg = get_reg_by_id(reg_id)
    if not reg:
        return None
    update_fields = []
    if name is not None:
        reg.name = name
        update_fields.append("name")
    if status is not None:
        reg.status = status
        update_fields.append("status")
    if update_fields:
        reg.ut = _now_ms()
        update_fields.append("ut")
        reg.save(using="verify_rw", update_fields=update_fields)
    return reg


def delete_reg(reg_id: int) -> bool:
    deleted, _ = Reg.objects.using("verify_rw").filter(id=reg_id).delete()
    return deleted > 0
