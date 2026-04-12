from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_tcc models to tcc_rw (sf_tcc)."""

    route_app_labels = frozenset({"app_tcc"})
    route_db_alias = "tcc_rw"
