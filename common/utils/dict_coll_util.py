def add_to_list(given_dict: dict, key, value):
    """
    Append value to dict list.

    @param given_dict: dict to be appended
    @param key: key of dict
    @param value: value to be appended
    """
    if not given_dict:
        pass
    if key not in given_dict:
        given_dict[key] = []
    given_dict[key].append(value)


def add_to_set(given_dict: dict, key, value):
    """
    Add a value into a set, one element of the given dict.

    @param given_dict: dict to be updated
    @param key: key of dict
    @param value: value to be added
    """
    if not given_dict:
        pass
    if key not in given_dict:
        given_dict[key] = set()
    given_dict[key].add(value)


def update_to_set(given_dict: dict, key, value_set: set):
    """
    Update a set of values into a set, one element of the given dict.

    @param given_dict: dict to be updated
    @param key: key of dict
    @param value_set: a set of values to be updated
    """
    if not given_dict:
        pass
    if key not in given_dict:
        given_dict[key] = set()
    given_dict[key].update(value_set)


def add_to_dict(given_dict: dict, key, value: dict):
    """
    Add a value into a dict, one element of the given dict.

    @param given_dict: dict to be updated
    @param key: key of dict
    @param value: value to be added
    """
    if not given_dict:
        pass
    if key not in given_dict:
        given_dict[key] = {}
    given_dict[key].update(value)


def add_to_dict_set(given_dict: dict, key, sub_key, value):
    """
    Add a value into a dict set, one element of the given dict.

    @param given_dict: dict to be updated
    @param key: key of dict
    @param sub_key: sub key of dict
    @param value: value to be added
    """
    if not given_dict:
        pass
    if key not in given_dict or given_dict[key] is None:
        given_dict[key] = {}
    if sub_key not in given_dict[key]:
        given_dict[key][sub_key] = set()
    given_dict[key][sub_key].add(value)


def update_to_dict_set(given_dict: dict, key, sub_key, value_set: set):
    """
    Update a set of values into a dict set, one element of the given dict.

    @param given_dict: dict to be updated
    @param key: key of dict
    @param sub_key: sub key of dict
    @param value_set: a set of values to be updated
    """
    if not given_dict:
        pass
    if key not in given_dict or given_dict[key] is None:
        given_dict[key] = {}
    if sub_key not in given_dict[key]:
        given_dict[key][sub_key] = set()
    given_dict[key][sub_key].update(value_set)
