from enum import IntEnum


class UserStatusEnum(IntEnum):
    DISABLED = 0
    ENABLED = 1

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

    @classmethod
    def values(cls):
        return [item.value for item in cls]
