"""
分类（classification）枚举：句子/知识点分类。
id 为数字，与 knowledge 表 classification 字段一致；供字典查询接口及业务逻辑使用。
"""


class ClassificationEnum:
    """分类枚举：id 为数字，k 为 code（展示/存储名），v 为 id 字符串（表单提交用）。"""

    CLAIM = 0
    FACT = 1
    EVENT = 2
    CONCEPT = 3
    DEFINITION = 4
    ARGUMENT = 5

    ITEMS = [
        (CLAIM, "claim"),
        (FACT, "fact"),
        (EVENT, "event"),
        (CONCEPT, "concept"),
        (DEFINITION, "definition"),
        (ARGUMENT, "argument"),
    ]

    CODE_TO_ID = {code: id_ for id_, code in ITEMS}

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": code, "v": id 字符串 }, ...]，下拉展示 k，提交用 v。"""
        return [{"k": code, "v": str(id_)} for id_, code in cls.ITEMS]
