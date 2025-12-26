from enum import Enum


class EventTypeEnum(Enum):
    SERVICE_START = 0
    SERVICE_STOP = 1
    CLOCK_BACKWARD = 2
    CONFIG_CHANGE = 3
    SEQUENCE_OVERFLOW = 4
    ERROR = 5
