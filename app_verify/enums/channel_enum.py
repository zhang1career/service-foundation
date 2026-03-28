from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("verify_channel")
class ChannelEnum(IntEnum):
    EMAIL = 0
    SMS = 1

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        return [
            {"k": "邮件", "v": str(cls.EMAIL)},
            {"k": "短信", "v": str(cls.SMS)},
        ]

    @classmethod
    def from_label(cls, label: str) -> int:
        mapping = {
            "email": cls.EMAIL,
            "sms": cls.SMS,
        }
        if not label:
            raise ValueError("channel is required")
        value = mapping.get(label.strip().lower())
        if value is None:
            raise ValueError("channel must be email or sms")
        return int(value)

    @classmethod
    def to_label(cls, value: int) -> str:
        mapping = {
            cls.EMAIL: "email",
            cls.SMS: "sms",
        }
        label = mapping.get(cls(value))
        return label
