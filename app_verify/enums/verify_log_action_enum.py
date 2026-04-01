from enum import IntEnum


class VerifyLogActionEnum(IntEnum):
    """verify_log.action：与业务含义绑定的稳定整型。"""

    CODE_REQUEST = 1
    CODE_CHECK = 2

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]
