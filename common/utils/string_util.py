def check_blank(param_str) -> bool:
    """
    判断是否为空字符串
    包括：None，""，"  "

    :param param_str: the string to be checked
    :return: bool
    """
    if param_str is None:
        return True
    return param_str == "" or param_str.strip() == ""


def lowercase(param_str: str) -> str:
    return param_str.lower()


def explode(data: str, symbol: str = ","):
    """
    逗号分隔（默认逗号）
    """
    if not data:
        return []
    return data.split(symbol)


def implode(item_list: list, symbol: str = ","):
    """
    Join items of a list by a specified symbol

    @param item_list:
    @param symbol:
    @return:
    """
    return symbol.join(str(item) for item in item_list)


def wrap_with_quotes(origin_str: str):
    """
    Wrap a string with double quotes

    @param origin_str: the string to be wrapped
    @return: wrapped string
    """
    return f'"{origin_str}"'


def wrap_with_quotes_batch(origin_list: list):
    """
    Wrap a list of strings with double quotes

    @param origin_list: the list of strings to be wrapped
    @return: wrapped list
    """
    return [wrap_with_quotes(origin_str) for origin_str in origin_list]


def truncate(df_str, max_length):
    """
    Truncate a string to a limited length

    @param df_str: the sting to be truncated
    @param max_length: the max length to preserve
    @return: truncated string
    """
    if max_length <= 2:
        raise Exception("max_length is too small")
    return (df_str[:max_length-2] + "..") if len(df_str) > max_length else df_str


def trim(origin_str: str):
    """
    Trim a string, removing leading and trailing whitespaces
    copy a new string

    @param origin_str: input string
    @return: trimmed string
    """
    return origin_str.strip()


def multi_line_to_single_line(origin_str: str):
    """
    Convert multi-line string to single-line string
    in-string replacement

    @param origin_str:
    @return:
    """
    return origin_str.replace("\n", " ")


def downcase_only_if_first_char_is_uppercase(input_str: str):
    """
    Convert the first character of a string to lowercase only if it is uppercase
    All characters uppercase will be ignored
    'Abc' -> 'abc'
    'def' -> 'def'
    'XYZ' -> 'XYZ'
    'p'   -> 'p'
    'Q'   -> 'Q'
    ''    -> None

    @param input_str:
    @return: (output_str, is_all_uppercase)
    """
    if not input_str:
        return None, None

    if len(input_str) <= 1:
        return input_str, input_str.isupper()

    uppercase_index_sum = 0
    for i in range(0, len(input_str)):
        char = input_str[i]
        if char.isupper():
            uppercase_index_sum += (i + 1)

    if uppercase_index_sum == 1:
        return input_str[0].lower() + input_str[1:], False
    return input_str, uppercase_index_sum >= (1 + len(input_str)) * len(input_str) / 2
