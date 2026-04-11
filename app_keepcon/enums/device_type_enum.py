"""Allowed values for ``KeepconDevice.device_type`` (integer column)."""
from __future__ import annotations

from enum import IntEnum


class KeepconDeviceType(IntEnum):
    """设备类型：与表 ``device.device_type`` 整型取值一致。"""

    MOBILE = 1
    WEB = 2
    IOT = 3

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]

    @classmethod
    def is_valid(cls, value: int) -> bool:
        return value in cls.values()

    @classmethod
    def normalize(cls, value: int | str) -> int:
        """Accept enum member, int in set, or legacy string mobile/web/iot."""
        if isinstance(value, cls):
            return int(value)
        if isinstance(value, int):
            if cls.is_valid(value):
                return value
            raise ValueError(f"device_type must be one of {cls.values()}, got {value}")
        s = str(value).strip().lower()
        legacy = {"mobile": cls.MOBILE, "web": cls.WEB, "iot": cls.IOT}
        if s in legacy:
            return int(legacy[s])
        if s.isdigit():
            v = int(s)
            if cls.is_valid(v):
                return v
        raise ValueError("device_type must be mobile|web|iot or 1|2|3")
