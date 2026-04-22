from __future__ import annotations

import logging
import re

from common.services.xxl_job import get_registry

logger = logging.getLogger(__name__)

_DEFAULT = 50
_LIMIT = re.compile(r"^\s*(\d{1,6})\s*$")


def _tcc_scan(params: str | None) -> tuple[bool, str]:
    from app_tcc.services.scan_service import claim_batch, process_one

    limit = _DEFAULT
    if params and params.strip():
        m = _LIMIT.match(params)
        if m:
            limit = int(m.group(1))
    if not 1 <= limit <= 1_000_000:
        return False, "limit out of range"

    rows = claim_batch(limit=limit)
    n = 0
    for g in rows:
        try:
            process_one(g)
            n += 1
        except Exception:
            logger.exception("tcc_scan xxl job global_tx_id=%s", g.pk)
    return True, f"limit={limit} ok={n} total={len(rows)}"


def register_tcc_jobs() -> None:
    get_registry().register("tccScan", _tcc_scan)
