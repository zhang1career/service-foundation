"""
阶段（stage）枚举：句子/知识点工作流阶段。
供字典查询接口及业务逻辑使用。
"""
from common.dict_catalog import register_dict_code


@register_dict_code("stage")
class StageEnum:
    """阶段枚举：k 为展示名，v 为 id 字符串；数值常量供代码引用。"""

    CREATE = 0
    PARSED = 1
    INGESTED = 2

    ITEMS = [
        (CREATE, "创建"),
        (PARSED, "已解析"),
        (INGESTED, "已入图"),
    ]

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": 展示名, "v": id 字符串 }, ...]。"""
        return [{"k": label, "v": str(id_)} for id_, label in cls.ITEMS]
