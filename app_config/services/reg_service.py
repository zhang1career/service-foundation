"""Caller registration for app_config; schedules cache bump on commit."""

from common.utils.django_util import schedule_on_commit

from app_config.repos import reg_repo
from app_config.services.config_cache_service import bump_config_cache_generation


def _to_dict(reg) -> dict:
    return {
        "id": reg.id,
        "name": reg.name,
        "access_key": reg.access_key,
        "status": reg.status,
        "ct": reg.ct,
        "ut": reg.ut,
    }


class ConfigRegService:
    @staticmethod
    def create_by_payload(payload: dict) -> dict:
        name = (payload.get("name") or "").strip()
        status = int(payload.get("status", 0))
        if not name:
            raise ValueError("name is required")
        reg = reg_repo.create_reg(name=name, status=status)
        schedule_on_commit(bump_config_cache_generation, reg.id)
        return _to_dict(reg)

    @staticmethod
    def list_all() -> list:
        return [_to_dict(item) for item in reg_repo.list_regs()]

    @staticmethod
    def get_one(reg_id: int) -> dict:
        reg = reg_repo.get_reg_by_id(reg_id)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict(reg)

    @staticmethod
    def update_by_payload(reg_id: int, payload: dict) -> dict:
        name = payload.get("name") if "name" in payload else None
        status = int(payload.get("status")) if "status" in payload else None
        reg = reg_repo.update_reg(reg_id=reg_id, name=name, status=status)
        if not reg:
            raise ValueError("reg not found")
        schedule_on_commit(bump_config_cache_generation, reg_id)
        return _to_dict(reg)

    @staticmethod
    def delete(reg_id: int) -> bool:
        reg = reg_repo.get_reg_by_id(reg_id)
        if not reg:
            raise ValueError("reg not found")
        rid = reg.id
        schedule_on_commit(bump_config_cache_generation, rid)
        ok = reg_repo.delete_reg(reg_id)
        if not ok:
            raise ValueError("reg not found")
        return True
