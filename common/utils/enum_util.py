def enum_contains(enum_class, item_name_str: str):
    return item_name_str in enum_class._member_names_


def enum_item_by_name(enum_class, item_name_str: str, default=None):
    if not enum_contains(enum_class, item_name_str):
        return default
    return enum_class[item_name_str]
