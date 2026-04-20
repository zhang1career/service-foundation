from __future__ import annotations

import logging

from django.db import transaction
from django.db.models import Q

from app_saga.enums import SagaInstanceStatus
from app_saga.models import SagaInstance
from app_saga.services.saga_coordinator import process_instance
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)


def claim_batch(*, limit: int = 20) -> list[SagaInstance]:
    now_ms = get_now_timestamp_ms()
    active = Q(
        status__in=[
            SagaInstanceStatus.RUNNING,
            SagaInstanceStatus.COMPENSATING,
        ]
    )
    due = Q(next_retry_at__lte=now_ms)
    with transaction.atomic(using="saga_rw"):
        qs = (
            SagaInstance.objects.using("saga_rw")
            .select_for_update(skip_locked=True)
            .filter(active & due)
            .order_by("next_retry_at")[:limit]
        )
        return list(qs)


def process_one(inst: SagaInstance) -> None:
    try:
        process_instance(inst.pk)
    except Exception:
        logger.exception("saga_scan failed instance_id=%s", inst.pk)
