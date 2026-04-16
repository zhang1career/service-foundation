"""config_entry.public column (sf_config.config_entry)."""

from enum import IntEnum


class ConfigEntryPublic(IntEnum):
    """0=private（按 condition 匹配）；1=public（不按 condition，condition 须为空字符串）。"""

    PRIVATE = 0
    PUBLIC = 1

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]
