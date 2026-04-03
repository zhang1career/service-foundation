from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for searchrec app to use searchrec_rw database."""

    route_app_labels = frozenset({"app_searchrec"})
    route_db_alias = "searchrec_rw"
