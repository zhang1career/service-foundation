"""
Distribution status enum - CDN 分发状态

存储于 d 表 status 字段，对应 CloudFront 状态值。
"""

from enum import IntEnum


class DistributionStatusEnum(IntEnum):
    """CDN 分发状态枚举，id 存储于 d.status 字段"""

    IN_PROGRESS = 0  # 配置中
    DEPLOYED = 1  # 已部署

    @classmethod
    def to_label(cls, status_id: int) -> str:
        """枚举 id 转为 CloudFront API 字符串。"""
        _map = {
            cls.IN_PROGRESS: "InProgress",
            cls.DEPLOYED: "Deployed",
        }
        return _map.get(status_id, "Deployed")

    @classmethod
    def from_label(cls, label: str) -> int:
        """CloudFront API 字符串转为枚举 id。"""
        _map = {
            "InProgress": cls.IN_PROGRESS,
            "Deployed": cls.DEPLOYED,
        }
        return _map.get(label, cls.DEPLOYED)
