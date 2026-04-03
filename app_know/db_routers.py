"""
Database router for app_know to use know_rw database.
Generated.
"""

from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_know models to know_rw database."""

    route_app_labels = frozenset({"app_know"})
    route_db_alias = "know_rw"
