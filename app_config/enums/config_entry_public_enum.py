"""config_entry.public column (sf_config.config_entry)."""

from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("config_entry_public")
class ConfigEntryPublic(IntEnum):
    """0=private（按 condition 匹配）；1=public（不按 condition，condition 须为空字符串）。"""

    PRIVATE = 0
    PUBLIC = 1

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [
            {
                "k": "按条件（private，参与 /ai/config/pri，按 condition 匹配）",
                "v": str(cls.PRIVATE.value),
            },
            {
                "k": "公开（public，无条件；仅 /api/config/pub 与 /ai/config/pri，condition 固定为空）",
                "v": str(cls.PUBLIC.value),
            },
        ]
