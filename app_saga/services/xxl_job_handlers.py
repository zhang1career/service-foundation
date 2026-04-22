from __future__ import annotations

import re

from common.services.xxl_job import get_registry

_DEFAULT = 50
_LIMIT = re.compile(r"^\s*(\d{1,6})\s*$")


def _saga_scan(params: str | None) -> tuple[bool, str]:
    from app_saga.services.scan_service import claim_batch, process_one

    limit = _DEFAULT
    if params and params.strip():
        m = _LIMIT.match(params)
        if m:
            limit = int(m.group(1))
    if not 1 <= limit <= 1_000_000:
        return False, "limit out of range"

    rows = claim_batch(limit=limit)
    for inst in rows:
        process_one(inst)
    return True, f"limit={limit} done={len(rows)}"


def register_saga_jobs() -> None:
    get_registry().register("sagaScan", _saga_scan)
