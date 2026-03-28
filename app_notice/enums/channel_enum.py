from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("notice_channel")
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
    def to_label(cls, value: int) -> str:
        return "email" if int(value) == cls.EMAIL else "sms"
