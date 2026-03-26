from enum import IntEnum


class VerifyLevelEnum(IntEnum):
    PASS = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def values(cls):
        return [item.value for item in cls]
