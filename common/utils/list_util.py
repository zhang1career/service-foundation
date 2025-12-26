def check_empty(data_list: list):
    if not data_list:
        return True
    return False


def list_first_element(data_list: list):
    data_list.sort()
    return data_list[0]


def column_of(dict_list: list[dict], field: str):
    """
    Column of

    If the field is not in the dict, the value will be ignored.

    CAUTION: There is no isolation between the input and the output, so the modification of output element will
    affect the input element.

    @param dict_list:
    @param field:
    @return:
    """
    # check param
    if not dict_list or not field:
        return []

    ret = []
    for _dict in dict_list:
        if field not in _dict:
            continue
        ret.append(_dict[field])
    return ret


def field_of(obj_list: list[object], field: str):
    ret = []
    for _obj in obj_list:
        if not hasattr(_obj, field):
            continue
        ret.append(getattr(_obj, field))
    return ret


def index_by(obj_list: list[dict], field: str) -> dict[any, dict]:
    """
    Index by field

    CAUTION: There is no isolation between the input and the output, so the modification of output element will
    affect the input element.

    @param obj_list:
    @param field:
    @return:
    """
    # check param
    if not obj_list or not field:
        return {}

    ret = {}
    for obj in obj_list:
        if field not in obj:
            continue
        ret[obj[field]] = obj
    return ret


def cartesian_product(list1: list, list2: list) -> list[tuple]:
    if not list1 or not list2:
        return []
    return [(x, y) for x in list1 for y in list2]


def append_and_unique_list(param_list: list, *param_var) -> list:
    """
    Append and unique list

    There is isolation between the input and the output, so the modification of output element will not affect the
    input.

    @param param_list:
    @param param_var:
    @return:
    """
    # lazy load
    from collections import OrderedDict
    # pre-check param
    if not param_list and not param_var:
        return []
    # filter param
    _var = list(filter(None, param_var))
    # check param
    if not param_list:
        return list(_var)
    # parameter isolation
    _list = list(param_list)
    # append
    _list.extend(_var)
    # unique
    return list(OrderedDict.fromkeys(_list))
