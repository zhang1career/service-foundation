"""
字典查询服务（兼容层）：委托 common.dict_catalog.get_dict_by_codes。
"""
from typing import Any, Dict, List

from common.dict_catalog import get_dict_by_codes as _get_dict_by_codes_impl


def get_dict_by_codes(codes: str) -> Dict[str, List[Dict[str, Any]]]:
    return _get_dict_by_codes_impl(codes)


__all__ = ["get_dict_by_codes"]
