"""
阶段（stage）枚举：句子/知识点工作流阶段。
供字典查询接口及业务逻辑使用。
"""


class StageEnum:
    """阶段枚举：k 为展示名，v 为 id 字符串；数值常量供代码引用。"""

    CREATED = 0
    CLEANED = 1
    PARSED = 2
    VECTORIZED = 3

    ITEMS = [
        (CREATED, "已创建"),
        (CLEANED, "已清洗"),
        (PARSED, "已解析"),
        (VECTORIZED, "已向量化"),
    ]

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": 展示名, "v": id 字符串 }, ...]。"""
        return [{"k": label, "v": str(id_)} for id_, label in cls.ITEMS]
