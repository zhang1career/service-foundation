"""Database router for app_cdn to use cdn database"""

from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_cdn models to cdn_rw database."""

    route_app_labels = frozenset({"app_cdn"})
    route_db_alias = "cdn_rw"
