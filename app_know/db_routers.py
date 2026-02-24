"""
Database router for app_know to use know_rw database.
Generated.
"""


class ReadWriteRouter:
    """Route app_know models to know_rw database."""

    route_app_labels = {"app_know"}
    route_db_alias = "know_rw"

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_db_alias
        return None
