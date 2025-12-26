from typing import Optional

from common.consts.string_const import STRING_EMPTY
from common.utils.hash_util import md5


def check_empty(param: Optional[dict]):
    """
    Check if a dictionary is empty.

    @param param: The dictionary to check.
    @return: True if the dictionary is None or empty, False otherwise.
    """
    if param is None:
        return True
    return not param


def get_first_key(param: dict):
    """
    Get the first key from a route map.

    @param param: The dictionary to get the first key from.
    @return:
    """
    if not param:
        return None
    return next(iter(param))


def get_key_list(param: dict) -> list:
    """
    Get all keys from a dictionary.

    @param param: The dictionary to get keys from.
    @return: A list of keys from the dictionary.
    """
    if check_empty(param):
        return []
    return list(param.keys())


def get_value_list(param: dict) -> list:
    """
    Get all values from a dictionary.

    @param param: The dictionary to get values from.
    @return: A list of values from the dictionary.
    """
    if check_empty(param):
        return []
    return list(param.values())


def dict_first_key(param: dict):
    sorted_keys = sorted(param)
    first_key = sorted_keys[0]
    return first_key


def dict_first_value(param: dict):
    first_key = dict_first_key(param)
    first_value = param[first_key]
    return first_value


def dict_first_pair(param: dict):
    first_key = dict_first_key(param)
    first_value = param[first_key]
    return first_key, first_value


def get_multiple_value_list(param_dict: dict, key_list: list) -> list:
    """
    Get multiple values from a dictionary by keys.

    @param param_dict: The dictionary to get values from.
    @param key_list: The list of keys to get values by.
    @return: A list of values from the dictionary.
    """
    if check_empty(param_dict):
        return []
    ret = []
    for key in key_list:
        if key not in param_dict:
            continue
        ret.append(param_dict[key])
    return ret


def get_multiple_value_dict(param_dict: dict, key_list: list) -> dict:
    """
    Get multiple values from a dictionary by keys.

    @param param_dict: The dictionary to get values from.
    @param key_list: The list of keys to get values by.
    @return: A list of values from the dictionary.
    """
    if check_empty(param_dict):
        return {}
    ret = {}
    for key in key_list:
        if key not in param_dict:
            continue
        ret[key] = param_dict[key]
    return ret


def columns_copy(original_dict: dict, columns: list[str]):
    """
    This function copies specified columns (keys) from an original dictionary to a new dictionary.

    @param original_dict: The original dictionary to copy from.
    @param columns: The list of keys to copy to the new dictionary.
    @return: A new dictionary containing only the specified keys.
    """
    new_dict = {key: original_dict[key] for key in columns if key in original_dict}
    return new_dict


def columns_copy_batch(original_dict_list: list[dict], columns: list[str]):
    new_dict_list = []
    for original_dict in original_dict_list:
        _new_dict = columns_copy(original_dict, columns)
        new_dict_list.append(_new_dict)

    return new_dict_list


def get_by_dict(given_dict: dict, key: dict):
    """
    Get value by dict as key.
    """
    tuple_key = build_key_from_dict(key)
    if tuple_key not in given_dict:
        return None
    return given_dict[tuple_key]


def set_by_dict(given_dict: dict, key: dict, value):
    """
    Set value by dict as key.
    """
    tuple_key = build_key_from_dict(key)
    given_dict[tuple_key] = value


def del_by_dict(given_dict: dict, key: dict):
    """
    Delete value by dict as key.
    """
    tuple_key = build_key_from_dict(key)
    del given_dict[tuple_key]


def build_key_from_dict(key: dict):
    return tuple(sorted(key.items()))


def merge(*dicts: dict):
    """
    Merge dicts.
    """
    # check param
    if not dicts:
        return {}
    # do merge
    ret = {}
    for _dict in dicts:
        ret.update(_dict)

    return ret


def invert(given_dict: dict):
    """
    Invert a dict.
    {1: "a", 2: "b"} => {"a": 1, "b": 2}
    """
    return {v: k for k, v in given_dict.items()}


def dict_by(data_list: list[dict], key: str) -> dict:
    """
    Build dict from list, by key.
    Elements that have a same key will be overwritten.

    @param data_list:
    @param key:
    @return:
    """
    if data_list is None or not data_list:
        return {}

    ret = {}
    for _data in data_list:
        if key not in _data:
            continue
        _value = _data[key]
        ret[_value] = _data
    return ret


def nest_clip(given_dict, given_key_list: list[str]) -> dict:
    """
    Clip nested dict by keys.

    CAUTION: There is no isolation between the input and the output, so the modification of output element will
    affect the input element.

    """
    # lazy load
    from common.utils.list_util import check_empty as list_check_empty

    if list_check_empty(given_key_list):
        return {}
    if not isinstance(given_dict, dict):
        return {}

    ret = {}
    # recursive
    if len(given_key_list) > 1:
        _ret = nest_clip(given_dict[given_key_list[0]], given_key_list[1:])
        if _ret:
            ret[given_key_list[0]] = _ret
        return ret
    # end
    given_key = given_key_list[0]
    if given_key not in given_dict:
        return {}
    return {
        given_key: given_dict[given_key]
    }


def sort_and_hash(param_dict: dict) -> tuple[dict, str]:
    """
    Sort and hash a dictionary.

    @param param_dict: The dictionary to sort and hash.
    @return: A tuple containing the sorted dictionary and the hash of the dictionary.
    """
    # lazy load
    from collections import OrderedDict

    if check_empty(param_dict):
        return {}, STRING_EMPTY

    sorted_param_dict = OrderedDict(sorted(param_dict.items()))
    hash_param = md5(str(sorted_param_dict))
    return sorted_param_dict, hash_param
