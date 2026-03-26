from enum import IntEnum


class ChannelEnum(IntEnum):
    EMAIL = 0
    SMS = 1

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_label(cls, value: int) -> str:
        return "email" if int(value) == cls.EMAIL else "sms"
