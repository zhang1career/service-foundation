from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for notice app to use notice_rw database."""

    route_app_labels = frozenset({"app_notice"})
    route_db_alias = "notice_rw"
