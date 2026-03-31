"""Type tags for nested ``param_specs`` trees (wire key ``t``) and flat coerce field ``type``."""

from enum import Enum

from common.dict_catalog import register_dict_code


class NestedParamType(str, Enum):
    """Stored values are UPPERCASE strings (wire JSON and DB ``param_specs``)."""

    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    ENUM = "ENUM"
    ARRAY = "ARRAY"
    OBJECT = "OBJECT"
    OBJECT_ARRAY = "OBJECT_ARRAY"

    @classmethod
    def branch_tag_values(cls) -> frozenset[str]:
        return frozenset({cls.OBJECT.value, cls.OBJECT_ARRAY.value})

    @classmethod
    def all_tag_values(cls) -> frozenset[str]:
        return frozenset(m.value for m in cls)


@register_dict_code("aibroker_nested_param_type")
class AibrokerNestedParamTypeDict:
    """HTTP dict / console: ``k`` and ``v`` are the same stored tag (uppercase)."""

    _ORDER = (
        NestedParamType.STRING,
        NestedParamType.INT,
        NestedParamType.FLOAT,
        NestedParamType.BOOL,
        NestedParamType.ENUM,
        NestedParamType.ARRAY,
        NestedParamType.OBJECT,
        NestedParamType.OBJECT_ARRAY,
    )

    @classmethod
    def to_dict_list(cls):
        return [{"k": e.value, "v": e.value} for e in cls._ORDER]
