from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("user_event_biz_type")
class EventBizTypeEnum(IntEnum):
    REGISTER = 1
    UPDATE_PROFILE = 2
    USER_AUTH = 3
    PASSWORD_RESET = 4

    @classmethod
    def to_dict_list(cls):
        labels = {
            cls.REGISTER: "注册",
            cls.UPDATE_PROFILE: "更新资料",
            cls.USER_AUTH: "用户认证",
            cls.PASSWORD_RESET: "密码重置",
        }
        return [{"k": labels[m], "v": str(m.value)} for m in cls]
