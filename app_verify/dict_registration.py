import app_verify.enums.channel_enum  # noqa: F401
import app_verify.enums.verify_level_enum  # noqa: F401

from common.dict_catalog import register_dict_code
from common.enums.service_reg_status_enum import ServiceRegStatus


@register_dict_code("verify_reg_status")
class VerifyRegStatusDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [
            {"k": "停用", "v": str(ServiceRegStatus.DISABLED.value)},
            {"k": "启用", "v": str(ServiceRegStatus.ENABLED.value)},
        ]
