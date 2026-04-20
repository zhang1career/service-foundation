from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_saga models to saga_rw (sf_saga)."""

    route_app_labels = frozenset({"app_saga"})
    route_db_alias = "saga_rw"
