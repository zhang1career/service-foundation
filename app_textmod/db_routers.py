from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for app_textmod → textmod_rw."""

    route_app_labels = frozenset({"app_textmod"})
    route_db_alias = "textmod_rw"
