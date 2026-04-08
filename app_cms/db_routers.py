"""Database router for app_cms to use the CMS database."""

from common.utils.django_db_router import AppLabelDatabaseRouter


class ReadWriteRouter(AppLabelDatabaseRouter):
    """Route app_cms models to the ``cms_rw`` database alias."""

    route_app_labels = frozenset({"app_cms"})
    route_db_alias = "cms_rw"
