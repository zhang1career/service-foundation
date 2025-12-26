def check_empty(data_set: set) -> bool:
    """
    Check if a set is empty

    @param data_set:
    @return:
    """
    return not data_set


def diff(origin_set: set, target_set: set) -> tuple[set, set]:
    """
    Diff set

    @param origin_set:
    @param target_set:
    @return: adding_set, removing_set
    """
    # check param
    if not origin_set and not target_set:
        return set(), set()
    if not origin_set:
        return target_set, set()
    if not target_set:
        return set(), origin_set

    return target_set - origin_set, origin_set - target_set
