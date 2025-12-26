from py2neo.cypher import Cursor


def extract_field(raw_result: Cursor, field: str):
    if not raw_result:
        return None
    begin_result_data = raw_result.data()
    if not begin_result_data or len(begin_result_data) < 1:
        return None
    begin_del_cnt = begin_result_data[0][field]
    return begin_del_cnt
