from enum import Enum

from common.dict_catalog import register_dict_code


@register_dict_code("snowflake_event_type")
class EventTypeEnum(Enum):
    SERVICE_START = 0
    SERVICE_STOP = 1
    CLOCK_BACKWARD = 2
    CONFIG_CHANGE = 3
    SEQUENCE_OVERFLOW = 4
    ERROR = 5

    @classmethod
    def to_dict_list(cls):
        labels = {
            cls.SERVICE_START: "服务启动",
            cls.SERVICE_STOP: "服务停止",
            cls.CLOCK_BACKWARD: "时钟回拨",
            cls.CONFIG_CHANGE: "配置变更",
            cls.SEQUENCE_OVERFLOW: "序列溢出",
            cls.ERROR: "错误",
        }
        return [{"k": labels.get(m, m.name), "v": str(m.value)} for m in cls]
