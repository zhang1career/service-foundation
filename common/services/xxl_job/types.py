from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class XxlRunRequest:
    job_id: int
    executor_handler: str
    executor_params: str | None
    log_id: int
    # Epoch ms; same as admin TriggerRequest.logDateTime / callback logDateTim (see JobThread).
    log_date_time_ms: int


def parse_run_body(data: dict[str, Any]) -> XxlRunRequest:
    job_id = int(data["jobId"])
    log_id = int(data["logId"])
    h = str(data["executorHandler"]).strip()
    if not h:
        raise ValueError("executorHandler must be non-empty")
    p = data.get("executorParams")
    params = None if p is None else (p if isinstance(p, str) else str(p))
    if job_id <= 0 or log_id <= 0:
        raise ValueError("jobId and logId must be positive")
    raw_ldt = data.get("logDateTime")
    if raw_ldt is None:
        log_date_time_ms = int(time.time() * 1000)
    else:
        log_date_time_ms = int(raw_ldt)
        if log_date_time_ms <= 0:
            raise ValueError("logDateTime must be positive")
    return XxlRunRequest(
        job_id=job_id,
        executor_handler=h,
        executor_params=params,
        log_id=log_id,
        log_date_time_ms=log_date_time_ms,
    )
