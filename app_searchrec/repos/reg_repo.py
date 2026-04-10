import uuid
from typing import Optional

from app_searchrec.models import SearchRecReg
from common.utils.date_util import get_now_timestamp_ms


def create_reg(name: str, status: int = 0) -> SearchRecReg:
    now_ms = get_now_timestamp_ms()
    return SearchRecReg.objects.using("searchrec_rw").create(
        name=name,
        access_key=uuid.uuid4().hex,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_regs():
    return list(SearchRecReg.objects.using("searchrec_rw").all().order_by("-id"))


def get_reg_by_id(reg_id: int) -> Optional[SearchRecReg]:
    return SearchRecReg.objects.using("searchrec_rw").filter(id=reg_id).first()


def get_reg_by_access_key_and_status(access_key: str, status: int) -> Optional[SearchRecReg]:
    return (
        SearchRecReg.objects.using("searchrec_rw")
        .filter(access_key=access_key, status=status)
        .first()
    )


def update_reg(reg_id: int, name: str = None, status: int = None) -> Optional[SearchRecReg]:
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
        reg.ut = get_now_timestamp_ms()
        update_fields.append("ut")
        reg.save(using="searchrec_rw", update_fields=update_fields)
    return reg


def delete_reg(reg_id: int) -> bool:
    deleted, _ = SearchRecReg.objects.using("searchrec_rw").filter(id=reg_id).delete()
    return deleted > 0
