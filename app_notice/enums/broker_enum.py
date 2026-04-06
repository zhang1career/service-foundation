from enum import IntEnum
from typing import Type

from common.dict_catalog import register_dict_code

from app_notice.enums.broker_jiang_enum import BrokerJiangEnum


@register_dict_code("notice_broker")
class BrokerEnum(IntEnum):
    UNDEFINED = 0
    JIANG = 1

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        return [
            {"k": "Server酱", "v": int(cls.JIANG)},
        ]

    @classmethod
    def to_broker(cls, raw_value: int) -> Type[BrokerJiangEnum]:
        value = int(raw_value)
        if value == cls.JIANG:
            return BrokerJiangEnum
        raise ValueError(f"unknown broker: {raw_value}")
