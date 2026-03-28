import json
import logging
import threading
import time

from app_aibroker.repos import create_job, get_asset_by_id, get_job_by_id, get_reg_by_id, update_job
from app_aibroker.services.callback_service import deliver_callback

logger = logging.getLogger(__name__)

JOB_PENDING = 0
JOB_RUNNING = 1
JOB_DONE = 2
JOB_FAILED = 3


def _run_job(job_id: int) -> None:
    job = get_job_by_id(job_id)
    if not job:
        return
    update_job(job_id, status=JOB_RUNNING)
    try:
        if job.job_type == "video_from_image":
            payload = json.loads(job.payload_json) if job.payload_json else {}
            asset_id = int(payload.get("input_asset_id", 0))
            asset = get_asset_by_id(asset_id) if asset_id else None
            if not asset or asset.reg_id != job.reg_id:
                raise ValueError("invalid input_asset_id")
            time.sleep(0.05)
            result = {
                "output_oss_bucket": payload.get("output_bucket", asset.oss_bucket),
                "output_oss_key": f"derived/video/{job_id}.mp4",
                "note": "stub transcode result; replace with real pipeline",
                "source": {"bucket": asset.oss_bucket, "key": asset.oss_key},
            }
            update_job(job_id, status=JOB_DONE, result_json=json.dumps(result))
        else:
            raise ValueError(f"unsupported job_type: {job.job_type}")
    except Exception as exc:
        logger.exception("[aibroker] job failed")
        msg = str(exc)
        update_job(job_id, status=JOB_FAILED, message=msg)

    job_final = get_job_by_id(job_id)
    reg_final = get_reg_by_id(job_final.reg_id) if job_final else None
    if job_final and job_final.callback_url and reg_final and reg_final.callback_secret:
        body = {
            "job_id": job_final.id,
            "reg_id": job_final.reg_id,
            "status": job_final.status,
            "event_type": "job_completed",
            "result": json.loads(job_final.result_json) if job_final.result_json else None,
            "message": job_final.message or "",
        }
        deliver_callback(job_final.callback_url, reg_final.callback_secret, body)


def enqueue_job(reg_id: int, job_type: str, payload: dict, callback_url: str) -> dict:
    job = create_job(reg_id, job_type, callback_url or "", payload)
    t = threading.Thread(target=_run_job, args=(job.id,), daemon=True)
    t.start()
    return {"job_id": job.id, "status": JOB_PENDING}


def job_to_dict(job) -> dict:
    return {
        "id": job.id,
        "reg_id": job.reg_id,
        "job_type": job.job_type,
        "status": job.status,
        "callback_url": job.callback_url,
        "payload_json": json.loads(job.payload_json) if job.payload_json else None,
        "result_json": json.loads(job.result_json) if job.result_json else None,
        "message": job.message,
        "ct": job.ct,
        "ut": job.ut,
    }
