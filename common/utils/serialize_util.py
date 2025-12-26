from common.utils.string_util import implode


def dict_to_text(data: dict):
    """
    Convert dict to text
    """
    # check param
    if not data:
        return ""

    text_list = []
    for key, value in data.items():
        text_list.append("{key}: {value}".format(key=key, value=value))
    return implode(text_list, "\n")
