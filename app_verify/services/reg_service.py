from app_verify.repos import (
    create_reg,
    list_regs,
    get_reg_by_id,
    update_reg,
    delete_reg,
)


def _to_dict(reg):
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
    def create_by_payload(payload: dict) -> dict:
        name = (payload.get("name") or "").strip()
        status = int(payload.get("status", 0))
        if not name:
            raise ValueError("name is required")
        reg = create_reg(name=name, status=status)
        return _to_dict(reg)

    @staticmethod
    def list_all() -> list:
        return [_to_dict(item) for item in list_regs()]

    @staticmethod
    def get_one(reg_id: int) -> dict:
        reg = get_reg_by_id(reg_id)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict(reg)

    @staticmethod
    def update_by_payload(reg_id: int, payload: dict) -> dict:
        name = payload.get("name") if "name" in payload else None
        status = int(payload.get("status")) if "status" in payload else None
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
