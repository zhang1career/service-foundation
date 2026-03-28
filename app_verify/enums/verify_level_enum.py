from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("verify_level")
class VerifyLevelEnum(IntEnum):
    PASS = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        labels = {
            cls.PASS: "通过",
            cls.LOW: "低",
            cls.MEDIUM: "中",
            cls.HIGH: "高",
        }
        return [{"k": labels[m], "v": str(m.value)} for m in cls]
