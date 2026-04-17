from __future__ import annotations

import logging
from importlib import import_module

from common.consts.result_const import RESULT_INDEX_MAP
from common.utils.json_util import json_encode, json_decode

logger = logging.getLogger(__name__)


def _allowed_module_func_pairs() -> frozenset[tuple[str, str]]:
    return frozenset((v["module"], v["func"]) for v in RESULT_INDEX_MAP.values())


def build_result_index(result_id, param_map: dict):
    """
    build result index dict

    :param result_id: the index of result
    :param param_map: the parameters for the index
    """
    query_info = RESULT_INDEX_MAP[result_id]

    return {
        # module
        "m": query_info["module"],
        # function
        "f": query_info["func"],
        # parameters
        "p": json_encode(param_map),
    }


def get_result(result_index: dict):
    """
    get result

    :param result_index: the index of result
    :return: (result, error_message)
    """
    module_name = result_index["m"]
    if not module_name:
        return None, "module name is empty"

    func_name = result_index["f"]
    if not func_name:
        return None, "function name is empty"

    if (module_name, func_name) not in _allowed_module_func_pairs():
        logger.warning(
            "get_result rejected module/func not in RESULT_INDEX_MAP m=%s f=%s",
            module_name,
            func_name,
        )
        return None, "result index is not allowed"

    param_map = None
    param_str = result_index["p"]
    if param_str:
        param_map = json_decode(param_str)

    try:
        module = import_module(module_name)
        func = getattr(module, func_name)
        result = func(param_map)
        return result, None
    except Exception:
        logger.exception("get_result failed for m=%s f=%s", module_name, func_name)
        return None, "execution failed"
