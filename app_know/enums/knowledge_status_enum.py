"""
知识状态（knowledge.status）枚举。
供字典查询接口及业务逻辑使用。
"""
from common.dict_catalog import register_dict_code


@register_dict_code("knowledge_status")
class KnowledgeStatusEnum:
    """知识状态：k 为展示名，v 为 id 字符串；数值常量供代码引用。"""

    INCOMPLETE = 0
    COMPLETED = 1
    PENDING_REVIEW = 2

    ITEMS = [
        (INCOMPLETE, "未完成"),
        (COMPLETED, "已完成"),
        (PENDING_REVIEW, "待复核"),
    ]

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": 展示名, "v": id 字符串 }, ...]。"""
        return [{"k": label, "v": str(id_)} for id_, label in cls.ITEMS]
