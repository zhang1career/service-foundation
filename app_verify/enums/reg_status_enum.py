from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("verify_reg_status")
class RegStatusEnum(IntEnum):
    DISABLED = 0
    ENABLED = 1

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [
            {"k": "停用", "v": str(cls.DISABLED.value)},
            {"k": "启用", "v": str(cls.ENABLED.value)},
        ]
