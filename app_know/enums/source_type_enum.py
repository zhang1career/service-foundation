"""
来源（source_type）枚举：批次来源类型。
与 app_know.consts.SOURCE_TYPE_* 一致，供字典查询接口使用。
"""
from common.dict_catalog import register_dict_code


@register_dict_code("source_type")
class SourceTypeEnum:
    """来源类型字典：k 为展示名，v 为 id 字符串（提交表单用）。"""

    ITEMS = [
        (0, "文字"),
        (1, "上传"),
    ]

    @classmethod
    def to_dict_list(cls):
        """返回 [{ "k": 展示名, "v": id 字符串 }, ...]。"""
        return [{"k": label, "v": str(id_)} for id_, label in cls.ITEMS]
