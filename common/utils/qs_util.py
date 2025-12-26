from django.db.models import QuerySet


def check_empty(qs: QuerySet) -> bool:
    if qs is None or not qs:
        return True
    return False
