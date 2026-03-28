"""Prompt template constraint_type (DB int) — dict code for APIs and console."""
from common.dict_catalog import register_dict_code


@register_dict_code("aibroker_constraint_type")
class AibrokerConstraintTypeEnum:
    """0 = weak, 1 = strong (output JSON key checks)."""

    WEAK = 0
    STRONG = 1

    ITEMS = [
        (WEAK, "弱"),
        (STRONG, "强"),
    ]

    @classmethod
    def to_dict_list(cls):
        return [{"k": label, "v": str(v)} for v, label in cls.ITEMS]
