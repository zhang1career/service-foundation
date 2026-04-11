from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_keepcon models to keepcon_rw database."""

    route_app_labels = frozenset({"app_keepcon"})
    route_db_alias = "keepcon_rw"
