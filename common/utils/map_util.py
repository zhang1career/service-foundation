import itertools

from django.db.models import QuerySet


def qs_to_df(data: QuerySet):
    """
    Convert QuerySet to DataFrame List
    """
    # lazy load
    from pandas import DataFrame

    return DataFrame(qs_to_dict_list(data))


def list_to_df(data: list):
    """
    Convert QuerySet to DataFrame List
    """
    # lazy load
    from pandas import DataFrame

    return DataFrame(data)


def group_to_df_list(data_dict: dict):
    """
    Convert dictionary list to DataFrame List
    """
    df_list = []
    for data in data_dict.values():
        _df = list_to_df(data)
        df_list.append(_df)
    return df_list


def qs_to_dict_list(data: QuerySet):
    """
    Convert QuerySet to Dict List
    @param data:
    @return:
    """
    return list(data.values())


def qs_to_dict_group(data: QuerySet, group_by: str):
    """
    Group QuerySet by field

    @param data: the QuerySet to be grouped
    @param group_by: the field by which to group the QuerySet
    @return: grouped
    """
    data_group = {}
    dict_list = list(data.values())
    for key, group in itertools.groupby(dict_list, key=lambda x: x[group_by]):
        data_group[key] = list(group)
    return data_group


def tuple_to_list(data: tuple):
    """
    Convert Tuple to List
    """
    if not data:
        return []
    return list(data)
