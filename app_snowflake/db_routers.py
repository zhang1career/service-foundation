class ReadWriteRouter:

    route_app_labels = {'app_snowflake'}
    route_db_alias = 'snowflake_rw'

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None  # None means use default database

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_db_alias
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True  # Allow relations if a model in the app is involved
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_db_alias
        return None
