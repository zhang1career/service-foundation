from __future__ import annotations

from enum import IntEnum


class SagaInstanceStatus(IntEnum):
    PENDING = 10
    RUNNING = 20
    CONFIRMING = 21
    COMPENSATING = 30
    COMPLETED = 40
    ROLLED_BACK = 50
    FAILED = 60


class SagaStepActionStatus(IntEnum):
    PENDING = 10
    SUCCEEDED = 20
    FAILED = 30


class SagaStepCompensateStatus(IntEnum):
    PENDING = 10
    SUCCEEDED = 20
    FAILED = 30
    SKIPPED = 40
