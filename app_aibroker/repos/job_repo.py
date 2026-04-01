import json
from typing import Optional

from app_aibroker.models import AiJob
from common.utils.date_util import get_now_timestamp_ms


def create_job(reg_id: int, job_type: str, callback_url: str, payload: dict) -> AiJob:
    now_ms = get_now_timestamp_ms()
    return AiJob.objects.using("aibroker_rw").create(
        reg_id=reg_id,
        job_type=job_type,
        status=0,
        callback_url=callback_url or "",
        payload_json=json.dumps(payload) if payload else None,
        ct=now_ms,
        ut=now_ms,
    )


def get_job_by_id(job_id: int) -> Optional[AiJob]:
    return AiJob.objects.using("aibroker_rw").filter(id=job_id).first()


def update_job(
    job_id: int,
    status: int = None,
    result_json: str = None,
    message: str = None,
) -> Optional[AiJob]:
    j = get_job_by_id(job_id)
    if not j:
        return None
    fields = []
    if status is not None:
        j.status = status
        fields.append("status")
    if result_json is not None:
        j.result_json = result_json
        fields.append("result_json")
    if message is not None:
        j.message = message[:512]
        fields.append("message")
    if fields:
        j.ut = get_now_timestamp_ms()
        fields.append("ut")
        j.save(using="aibroker_rw", update_fields=fields)
    return j
