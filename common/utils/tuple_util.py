def append_and_unique_tuple(param_list: list, *param_var) -> tuple:
    """
    Append and unique tuple

    @param param_list:
    @param param_var:
    @return:
    """
    # lazy load
    from common.utils.list_util import append_and_unique_list

    unique_list = append_and_unique_list(param_list, *param_var)
    return tuple(unique_list)
