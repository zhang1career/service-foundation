def replace_char(raw_string: str, replace_dict: dict[str, str]) -> str:
    """
    Replace characters in a string based on a dictionary of replacements.

    Args:
        raw_string (str): The input string to be filtered.
        replace_dict (dict[str, str]): A dictionary where keys are characters to be replaced
                                        and values are the characters to replace with.

    Returns:
        str: The filtered string with characters replaced according to the dictionary.
    """
    ret_str = ""
    for c in raw_string:
        if c not in replace_dict:
            ret_str += c
            continue
        ret_str += replace_dict[c]
    return ret_str
