from enum import IntEnum


class EventStatusEnum(IntEnum):
    INIT = 0
    PENDING_VERIFY = 1
    COMPLETED = 3
    FAILED = 9
