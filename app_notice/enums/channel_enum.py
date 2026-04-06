from enum import IntEnum

from common.dict_catalog import register_dict_code
from common.exceptions import InvalidArgumentError


@register_dict_code("notice_channel")
class ChannelEnum(IntEnum):
    EMAIL = 0
    SMS = 1
    WECHAT_SERVICE = 10
    WECOM_GROUP = 22
    WECOM_APP = 23
    DINGDING_GROUP = 32
    LARK_GROUP = 42

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def to_dict_list(cls):
        return [
            {"k": "邮件", "v": int(cls.EMAIL)},
            {"k": "短信", "v": int(cls.SMS)},
            {"k": "微信服务号", "v": int(cls.WECHAT_SERVICE)},
            {"k": "企业微信群机器人", "v": int(cls.WECOM_GROUP)},
            {"k": "企业微信应用消息", "v": int(cls.WECOM_APP)},
            {"k": "钉钉群机器人", "v": int(cls.DINGDING_GROUP)},
            {"k": "飞书群机器人", "v": int(cls.LARK_GROUP)},
        ]

    @classmethod
    def to_label(cls, raw_value: int) -> str:
        value = int(raw_value)
        if value == cls.EMAIL:
            return "email"
        if value == cls.SMS:
            return "sms"
        if value == cls.WECHAT_SERVICE:
            return "wechat_service"

        if value == cls.WECOM_GROUP:
            return "wecom_group"
        if value == cls.WECOM_APP:
            return "wecom_app"
        if value == cls.DINGDING_GROUP:
            return "dingding_group"
        if value == cls.LARK_GROUP:
            return "lark_group"
        raise InvalidArgumentError(f"the value {raw_value} is not supported")
