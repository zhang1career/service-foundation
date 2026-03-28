from enum import Enum

from common.dict_catalog import register_dict_code


@register_dict_code("foundation_app")
class AppEnum(Enum):
    APP_STOCK = 1

    @classmethod
    def to_dict_list(cls):
        return [{"k": m.name.replace("_", " "), "v": str(m.value)} for m in cls]
