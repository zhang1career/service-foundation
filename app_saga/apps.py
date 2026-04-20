from django.apps import AppConfig


class AppSagaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_saga"
    label = "app_saga"
    verbose_name = "Saga 编排"
