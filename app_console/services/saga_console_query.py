from __future__ import annotations

from app_saga.models import SagaFlow, SagaInstance, SagaStepRun

from app_console.services.dict_options import CODE_SAGA_INSTANCE_STATUS, int_kv


def list_instances(*, status: int | None, page: int, page_size: int) -> tuple[int, list[SagaInstance]]:
    qs = SagaInstance.objects.using("saga_rw").select_related("flow").order_by("-id")
    if status is not None:
        qs = qs.filter(status=status)
    total = qs.count()
    off = max(0, (page - 1) * page_size)
    rows = list(qs[off : off + page_size])
    return total, rows


def get_instance(instance_id: int) -> SagaInstance | None:
    return (
        SagaInstance.objects.using("saga_rw")
        .select_related("flow", "participant")
        .filter(pk=instance_id)
        .first()
    )


def list_step_runs(instance_id: int):
    return list(
        SagaStepRun.objects.using("saga_rw")
        .select_related("flow_step")
        .filter(instance_id=instance_id)
        .order_by("step_index", "id")
    )


def get_flow_for_console(flow_id: int) -> SagaFlow | None:
    return (
        SagaFlow.objects.using("saga_rw")
        .select_related("participant")
        .filter(pk=flow_id)
        .first()
    )


def list_status_options():
    return int_kv(CODE_SAGA_INSTANCE_STATUS)
