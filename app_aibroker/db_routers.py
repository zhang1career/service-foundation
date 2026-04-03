from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for app_aibroker → aibroker_rw"""

    route_app_labels = frozenset({"app_aibroker"})
    route_db_alias = "aibroker_rw"
