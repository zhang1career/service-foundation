from common.utils.hash_util import md5


def sort_and_hash(string_list: list[str]) -> tuple[list[str], str]:
    """
    Sorts a list of strings and calculates the hash of the sorted list.

    @param string_list: List of strings to be sorted and hashed
    @return: A tuple containing the sorted list and the hash value
    """
    # sort the list
    sorted_list = sorted(string_list)
    joined_string = ''.join(sorted_list)

    return sorted_list, md5(joined_string)


def column_of_first_char(string_list: list[str]) -> list[str]:
    """
    Returns the first character of each string in the list.
    Empty member in argument list will be ignored.
    """
    return [s[0] for s in string_list if s]


def index_by_first_char(string_list: list[str]) -> dict[str, list[str]]:
    """
    Returns the first character indexed list.
    When the first character is the same, the strings will be grouped to a list as original order.
    Empty member in argument list will be ignored.
    """
    ret_dict = {}
    for s in string_list:
        if not s:
            continue
        ret_dict.setdefault(s[0], []).append(s)
    return ret_dict
