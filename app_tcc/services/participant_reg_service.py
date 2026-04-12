from __future__ import annotations

import uuid

from django.db import transaction

from app_tcc.models import TccParticipant
from common.enums.service_reg_status_enum import ServiceRegStatus


def list_participants():
    return list(TccParticipant.objects.using("tcc_rw").all().order_by("id"))


def get_participant_by_id(pk: int) -> TccParticipant | None:
    return TccParticipant.objects.using("tcc_rw").filter(pk=pk).first()


def _build_participant_for_insert(
    *,
    access_key: str,
    name: str,
    status: int,
) -> TccParticipant:
    return TccParticipant(
        access_key=access_key.strip(),
        name=(name or "").strip(),
        status=status,
    )


@transaction.atomic(using="tcc_rw")
def create_participant(
    *,
    name: str,
    status: int = ServiceRegStatus.ENABLED.value,
) -> TccParticipant:
    access_key = uuid.uuid4().hex
    p = _build_participant_for_insert(
        access_key=access_key,
        name=name,
        status=status,
    )
    p.save(using="tcc_rw")
    return p


@transaction.atomic(using="tcc_rw")
def update_participant(
    pk: int,
    *,
    access_key: str | None = None,
    name: str | None = None,
    status: int | None = None,
) -> TccParticipant | None:
    p = TccParticipant.objects.using("tcc_rw").filter(pk=pk).first()
    if not p:
        return None
    if access_key is not None:
        p.access_key = access_key.strip()
    if name is not None:
        p.name = name.strip()
    if status is not None:
        p.status = int(status)
    p.save(using="tcc_rw")
    return p


@transaction.atomic(using="tcc_rw")
def delete_participant(pk: int) -> bool:
    deleted, _ = TccParticipant.objects.using("tcc_rw").filter(pk=pk).delete()
    return deleted > 0
