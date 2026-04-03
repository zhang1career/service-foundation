from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for user app to use user_rw database."""

    route_app_labels = frozenset({"app_user"})
    route_db_alias = "user_rw"
