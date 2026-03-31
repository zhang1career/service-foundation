from enum import Enum


class AigcInvokeOp(str, Enum):
    """AigcAPI.invoke branch; names align with ModelCapabilityEnum."""

    CHAT = "CHAT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    EMBEDDING = "EMBEDDING"
