"""通知记录发送结果：与 notice 表 status 字段一致（0 未成功含排队/失败，1 成功）。"""

from common.dict_catalog import register_dict_code


@register_dict_code("notice_status")
class NoticeStatusDict:
    @classmethod
    def to_dict_list(cls):
        return [
            {"k": "未成功", "v": 0},
            {"k": "成功", "v": 1},
        ]
