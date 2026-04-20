from __future__ import annotations

import uuid

from django.db import transaction

from app_saga.models import SagaParticipant
from common.enums.service_reg_status_enum import ServiceRegStatus


def list_participants():
    return list(SagaParticipant.objects.using("saga_rw").all().order_by("id"))


def get_participant_by_id(pk: int) -> SagaParticipant | None:
    return SagaParticipant.objects.using("saga_rw").filter(pk=pk).first()


def get_participant_by_access_key(access_key: str) -> SagaParticipant | None:
    k = (access_key or "").strip()
    if not k:
        return None
    return SagaParticipant.objects.using("saga_rw").filter(access_key=k).first()


@transaction.atomic(using="saga_rw")
def create_participant(
        *,
        name: str,
        status: int = ServiceRegStatus.ENABLED.value,
) -> SagaParticipant:
    access_key = uuid.uuid4().hex
    p = SagaParticipant(
        access_key=access_key,
        name=(name or "").strip(),
        status=status,
    )
    p.save(using="saga_rw")
    return p


@transaction.atomic(using="saga_rw")
def update_participant(
        pk: int,
        *,
        access_key: str | None = None,
        name: str | None = None,
        status: int | None = None,
) -> SagaParticipant | None:
    p = SagaParticipant.objects.using("saga_rw").filter(pk=pk).first()
    if not p:
        return None
    if access_key is not None:
        p.access_key = access_key.strip()
    if name is not None:
        p.name = name.strip()
    if status is not None:
        p.status = int(status)
    p.save(using="saga_rw")
    return p


@transaction.atomic(using="saga_rw")
def delete_participant(pk: int) -> bool:
    deleted, _ = SagaParticipant.objects.using("saga_rw").filter(pk=pk).delete()
    return deleted > 0
