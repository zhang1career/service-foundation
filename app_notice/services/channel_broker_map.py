"""ChannelEnum.id → broker-specific channel id (e.g. BrokerJiangEnum) by matching member names."""
from __future__ import annotations

from enum import IntEnum

from app_notice.enums import ChannelEnum
from common.utils.dict_util import map_dict_values_by_shared_keys

_map_cache: dict[type[IntEnum], dict[int, int]] = {}


def channel_to_broker_channel_ids(broker_enum_cls: type[IntEnum]) -> dict[int, int]:
    """Map ChannelEnum value → broker enum value for members that share the same name."""
    cached = _map_cache.get(broker_enum_cls)
    if cached is not None:
        return cached
    left = _enum_name_to_value(ChannelEnum)
    right = _enum_name_to_value(broker_enum_cls)
    out = map_dict_values_by_shared_keys(left, right)
    _map_cache[broker_enum_cls] = out
    return out


def _enum_name_to_value(enum_cls: type[IntEnum]) -> dict[str, int]:
    return {name: int(member.value) for name, member in enum_cls.__members__.items()}
