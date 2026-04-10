from __future__ import annotations

from typing import Any

from common.enums.service_reg_status_enum import ServiceRegStatus
from app_verify.models import Reg
from app_verify.repos import (
    create_reg,
    list_regs,
    get_reg_by_id,
    update_reg,
    delete_reg,
)


def _parse_reg_status(raw) -> int:
    try:
        return int(ServiceRegStatus(int(raw)))
    except ValueError:
        raise ValueError(f"status must be one of {ServiceRegStatus.values()}") from None


def _to_dict(reg: Reg) -> dict[str, Any]:
    return {
        "id": reg.id,
        "name": reg.name,
        "access_key": reg.access_key,
        "status": reg.status,
        "ct": reg.ct,
        "ut": reg.ut,
    }


class RegService:
    @staticmethod
    def create_by_payload(payload: dict) -> dict[str, Any]:
        name = (payload.get("name") or "").strip()
        status = _parse_reg_status(payload.get("status", ServiceRegStatus.DISABLED.value))
        if not name:
            raise ValueError("name is required")
        reg = create_reg(name=name, status=status)
        return _to_dict(reg)

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        return [_to_dict(item) for item in list_regs()]

    @staticmethod
    def get_one(reg_id: int) -> dict[str, Any]:
        reg = get_reg_by_id(reg_id)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict(reg)

    @staticmethod
    def update_by_payload(reg_id: int, payload: dict) -> dict[str, Any]:
        name = payload.get("name") if "name" in payload else None
        status = _parse_reg_status(payload["status"]) if "status" in payload else None
        reg = update_reg(reg_id=reg_id, name=name, status=status)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict(reg)

    @staticmethod
    def delete(reg_id: int) -> bool:
        ok = delete_reg(reg_id)
        if not ok:
            raise ValueError("reg not found")
        return True
