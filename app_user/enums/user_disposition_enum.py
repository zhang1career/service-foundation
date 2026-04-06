from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("user_disposition")
class UserDispositionEnum(IntEnum):
    """Security / ops disposition; 0 = none (normal)."""

    NONE = 0
    LOGIN_FORBIDDEN = 1

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        labels = {
            cls.NONE: "无",
            cls.LOGIN_FORBIDDEN: "禁止登录",
        }
        return [{"k": labels[m], "v": str(m.value)} for m in cls]
