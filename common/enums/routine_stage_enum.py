from enum import Enum

from common.dict_catalog import register_dict_code


@register_dict_code("routine_stage")
class RoutineStageEnum(Enum):
    CALC = 0
    REPORT = 1
    SUMMARY = 2

    @classmethod
    def to_dict_list(cls):
        labels = {
            cls.CALC: "计算",
            cls.REPORT: "报告",
            cls.SUMMARY: "汇总",
        }
        return [{"k": labels.get(m, m.name), "v": str(m.value)} for m in cls]
