"""
分类（classification）枚举：句子/知识点分类。
与 app_know.consts.CLASS_CHOICES 一致，供字典查询接口使用。
"""


class ClassificationEnum:
    """分类字典：k 为展示名，v 为存储值（提交表单用）。"""

    ITEMS = [
        ("claim", "Claim"),
        ("fact", "Fact"),
        ("event", "Event"),
        ("concept", "Concept"),
        ("definition", "Definition"),
        ("argument", "Argument"),
    ]

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": 展示名, "v": 存储值 }, ...]，下拉展示 k，提交用 v。"""
        return [{"k": label, "v": code} for code, label in cls.ITEMS]
