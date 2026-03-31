def create_reg(*, name: str, status: int):
    from app_aibroker.repos.reg_repo import create_reg as _impl

    return _impl(name=name, status=status)


def list_regs():
    from app_aibroker.repos.reg_repo import list_regs as _impl

    return _impl()


def get_reg_by_id(reg_id: int):
    from app_aibroker.repos.reg_repo import get_reg_by_id as _impl

    return _impl(reg_id)


def update_reg(*, reg_id: int, name, status):
    from app_aibroker.repos.reg_repo import update_reg as _impl

    return _impl(reg_id=reg_id, name=name, status=status)


def delete_reg(reg_id: int):
    from app_aibroker.repos.reg_repo import delete_reg as _impl

    return _impl(reg_id)


def _to_dict(reg, include_secrets_on_create: bool = False):
    d = {
        "id": reg.id,
        "name": reg.name,
        "status": reg.status,
        "ct": reg.ct,
        "ut": reg.ut,
    }
    if include_secrets_on_create:
        d["access_key"] = reg.access_key
        d["callback_secret"] = reg.callback_secret
    return d


def _to_dict_masked(reg):
    return {
        "id": reg.id,
        "name": reg.name,
        "access_key": reg.access_key[:8] + "…" if reg.access_key else "",
        "status": reg.status,
        "ct": reg.ct,
        "ut": reg.ut,
    }


def _to_dict_console(reg):
    """管理后台列表用：与 notice/verify 控制台一致展示完整 access_key。"""
    return {
        "id": reg.id,
        "name": reg.name,
        "access_key": reg.access_key or "",
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
        return _to_dict(reg, include_secrets_on_create=True)

    @staticmethod
    def list_all() -> list:
        return [_to_dict_masked(item) for item in list_regs()]

    @staticmethod
    def list_all_for_console() -> list:
        return [_to_dict_console(item) for item in list_regs()]

    @staticmethod
    def get_one(reg_id: int) -> dict:
        reg = get_reg_by_id(reg_id)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict_masked(reg)

    @staticmethod
    def update_by_payload(reg_id: int, payload: dict) -> dict:
        name = payload.get("name") if "name" in payload else None
        status = int(payload.get("status")) if "status" in payload else None
        reg = update_reg(reg_id=reg_id, name=name, status=status)
        if not reg:
            raise ValueError("reg not found")
        return _to_dict_masked(reg)

    @staticmethod
    def delete(reg_id: int) -> bool:
        ok = delete_reg(reg_id)
        if not ok:
            raise ValueError("reg not found")
        return True
