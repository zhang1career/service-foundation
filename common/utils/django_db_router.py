"""Reusable Django database router: one alias for a fixed set of app labels."""


class AppLabelDatabaseRouter:
    """Subclass and set ``route_app_labels`` and ``route_db_alias``."""

    route_app_labels: frozenset[str] = frozenset()
    route_db_alias: str = ""

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in self.route_app_labels or obj2._meta.app_label in self.route_app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_db_alias
        return None
