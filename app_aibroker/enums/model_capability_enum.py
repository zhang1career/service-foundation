"""AiModel.capability values (DB smallint)."""
from enum import IntEnum

from common.dict_catalog import register_dict_code
from common.enums.aigc_invoke_op_enum import AigcInvokeOp


class ModelCapabilityEnum(IntEnum):
    """0 chat, 1 image, 2 video, 3 embedding — matches ai_model field comment."""

    CHAT = 0
    IMAGE = 1
    VIDEO = 2
    EMBEDDING = 3

    @classmethod
    def aigc_invoke_op(cls, capability: int) -> AigcInvokeOp:
        """Map ai_model.capability to AigcAPI.invoke op (names match AigcInvokeOp)."""
        try:
            cap = cls(capability)
        except ValueError as e:
            raise ValueError(f"invalid ai_model.capability: {capability!r}") from e
        return AigcInvokeOp[cap.name]


@register_dict_code("aibroker_model_capability")
class AibrokerModelCapabilityDict:
    """HTTP dict / console: k=display name, v=stored capability id (str)."""

    ITEMS = [
        (ModelCapabilityEnum.CHAT, "对话"),
        (ModelCapabilityEnum.IMAGE, "图像"),
        (ModelCapabilityEnum.VIDEO, "视频"),
        (ModelCapabilityEnum.EMBEDDING, "向量"),
    ]

    @classmethod
    def to_dict_list(cls):
        return [{"k": label, "v": str(v)} for v, label in cls.ITEMS]
