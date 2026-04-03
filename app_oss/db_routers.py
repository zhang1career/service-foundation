from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for OSS app to use oss_rw database."""

    route_app_labels = frozenset({"app_oss"})
    route_db_alias = "oss_rw"
