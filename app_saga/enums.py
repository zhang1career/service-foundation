from __future__ import annotations

from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("saga_instance_status")
class SagaInstanceStatus(IntEnum):
    PENDING = 10
    RUNNING = 20
    CONFIRMING = 21
    COMPENSATING = 30
    COMPLETED = 40
    ROLLED_BACK = 50
    FAILED = 60

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [{"k": m.name, "v": str(m.value)} for m in cls]


@register_dict_code("saga_step_action_status")
class SagaStepActionStatus(IntEnum):
    PENDING = 10
    SUCCEEDED = 20
    FAILED = 30

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [{"k": m.name, "v": str(m.value)} for m in cls]


@register_dict_code("saga_step_compensate_status")
class SagaStepCompensateStatus(IntEnum):
    PENDING = 10
    SUCCEEDED = 20
    FAILED = 30
    SKIPPED = 40

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [{"k": m.name, "v": str(m.value)} for m in cls]
