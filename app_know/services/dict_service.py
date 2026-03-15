"""
字典查询服务：根据 codes 解析并返回各字典项数据。
支持两种定义方式：1）枚举类 app_know/enums/{Name}Enum；2）函数拦截（可扩展）。
返回格式：{ "code": [ { "k": 展示值, "v": 提交值 }, ... ], ... }
"""
import importlib
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _code_to_enum_class_name(code: str) -> str:
    """code 转枚举类名：classification -> ClassificationEnum, source_type -> SourceTypeEnum"""
    if not code or not code.strip():
        return ""
    parts = (code.strip()).split("_")
    return "".join(p.capitalize() for p in parts) + "Enum"


def _code_to_enum_module_name(code: str) -> str:
    """code 转枚举模块名：classification -> classification_enum, source_type -> source_type_enum"""
    if not code or not code.strip():
        return ""
    return (code.strip()).lower() + "_enum"


def _get_enum_dict_list(code: str) -> List[Dict[str, Any]]:
    """
    尝试从 app_know.enums 加载 {Code}Enum 类并返回 to_dict_list()。
    若模块或类不存在、或无 to_dict_list 则返回 None。
    """
    class_name = _code_to_enum_class_name(code)
    module_name = _code_to_enum_module_name(code)
    if not class_name or not module_name:
        return None
    try:
        mod = importlib.import_module(f"app_know.enums.{module_name}")
        cls = getattr(mod, class_name, None)
        if cls is None:
            return None
        method = getattr(cls, "to_dict_list", None)
        if method is None or not callable(method):
            return None
        result = method()
        if not isinstance(result, list):
            return None
        return result
    except Exception as e:
        logger.debug("[dict_service] enum load for code=%s: %s", code, e)
        return None


def get_dict_by_codes(codes: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    根据逗号分隔的 codes 查询字典数据。
    仅当某 code 存在枚举定义或函数拦截结果时才加入返回；忽略不存在的 code。
    返回形如：{ "classification": [ { "k": "Claim", "v": "claim" }, ... ], "source_type": [ ... ] }
    """
    if not codes or not isinstance(codes, str):
        return {}
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    result = {}
    for code in code_list:
        # 1) 可扩展：函数拦截（如 misc_service.classification(cond)）
        # 2) 枚举类：app_know/enums/{Name}Enum
        items = _get_enum_dict_list(code)
        if items is not None:
            result[code] = items
    return result
