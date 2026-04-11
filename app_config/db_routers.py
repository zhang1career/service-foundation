from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_config models to config_rw database."""

    route_app_labels = frozenset({"app_config"})
    route_db_alias = "config_rw"
