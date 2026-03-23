"""
Invalidation status enum - CDN 缓存失效状态

存储于 invalid 表 status 字段，对应 CloudFront 状态值。
"""

from enum import IntEnum


class InvalidationStatusEnum(IntEnum):
    """缓存失效状态枚举，id 存储于 invalid.status 字段"""

    IN_PROGRESS = 0  # 处理中
    COMPLETED = 1  # 已完成

    @classmethod
    def to_label(cls, status_id: int) -> str:
        """枚举 id 转为 CloudFront API 字符串。"""
        _map = {
            cls.IN_PROGRESS: "InProgress",
            cls.COMPLETED: "Completed",
        }
        return _map.get(status_id, "Completed")

    @classmethod
    def from_label(cls, label: str) -> int:
        """CloudFront API 字符串转为枚举 id。"""
        _map = {
            "InProgress": cls.IN_PROGRESS,
            "Completed": cls.COMPLETED,
        }
        return _map.get(label, cls.COMPLETED)
