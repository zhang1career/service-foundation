import hashlib
import json
from typing import Optional

from app_aibroker.models import AiIdempotency
from common.utils.date_util import get_now_timestamp_ms


def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_idempotency(reg_id: int, idempotency_key: str) -> Optional[AiIdempotency]:
    return (
        AiIdempotency.objects.using("aibroker_rw")
        .filter(reg_id=reg_id, idem_key=idempotency_key)
        .first()
    )


def save_idempotency(reg_id: int, idempotency_key: str, payload: dict, response_obj: dict) -> AiIdempotency:
    return AiIdempotency.objects.using("aibroker_rw").create(
        reg_id=reg_id,
        idem_key=idempotency_key,
        req_hash=_hash_payload(payload),
        resp_json=json.dumps(response_obj),
        ct=get_now_timestamp_ms(),
    )
