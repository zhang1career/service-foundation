from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for verify app to use verify_rw database."""

    route_app_labels = frozenset({"app_verify"})
    route_db_alias = "verify_rw"
