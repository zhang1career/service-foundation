from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("user_status")
class UserStatusEnum(IntEnum):
    DISABLED = 0
    ENABLED = 1

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        labels = {cls.DISABLED: "禁用", cls.ENABLED: "启用"}
        return [{"k": labels[m], "v": str(m.value)} for m in cls]
