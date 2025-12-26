from typing import Callable


# todo: merge with field_of ?
def prop_of(obj_list: list[object], field: str) -> list:
    """
    Get a property from a list of objects.

    If the field is not in the object, the value will be ignored.

    @param obj_list:
    @param field:
    @return:
    """
    # lazy load
    from common.utils.list_util import check_empty

    # check param
    if check_empty(obj_list):
        return []

    ret = []
    for _obj in obj_list:
        if not _obj:
            continue
        ret.append(getattr(_obj, field, None))
    return ret


def map_of(func: Callable, obj_list: list[object]) -> list:
    """
    Map a function to a list of objects.
    Field absent will be None.

    @param func:
    @param obj_list:
    @return:
    """
    # lazy load
    from common.utils.list_util import check_empty

    # check param
    if check_empty(obj_list):
        return []

    ret = []
    for _obj in obj_list:
        if not _obj:
            ret.append(None)
            continue
        ret.append(func(_obj))
    return ret
