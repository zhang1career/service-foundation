from common.utils.string_util import implode


def build_mask_in_cond(tag_count):
    """
    Build the IN condition for SQL query
    n items -> "%s,%s,%s,...,%s"

    @param tag_count:
    @return:
    """
    _tag_template = ["%s"] * tag_count
    _tag_list = implode(_tag_template, ",")
    return _tag_list


def raw_query(sql, param_list):
    # lazy load
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(sql, param_list)
        fetchall = cursor.fetchall()
        if not fetchall:
            return []

    return fetchall_to_list(cursor, fetchall)


def fetchall_to_list(cursor, fetchall):
    # Convert the results to a list of dictionaries
    result_list = []
    for row in fetchall:
        result_list.append(dict(zip([col[0] for col in cursor.description], row)))
    return result_list
