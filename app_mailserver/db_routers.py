from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for mailserver app to use mailserver_rw database."""

    route_app_labels = frozenset({"app_mailserver"})
    route_db_alias = "mailserver_rw"
