from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Database router for snowflake app to use snowflake_rw database."""

    route_app_labels = frozenset({"app_snowflake"})
    route_db_alias = "snowflake_rw"
