from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class XxlRunRequest:
    job_id: int
    executor_handler: str
    executor_params: str | None
    log_id: int


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
    return XxlRunRequest(
        job_id=job_id,
        executor_handler=h,
        executor_params=params,
        log_id=log_id,
    )
