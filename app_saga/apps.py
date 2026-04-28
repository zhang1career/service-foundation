from django.apps import AppConfig


class AppSagaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_saga"
    label = "app_saga"
    verbose_name = "Saga 编排"

    def ready(self) -> None:
        import app_saga.dict_registration  # noqa: F401

        from app_saga.services import xxl_job_handlers

        xxl_job_handlers.register_saga_jobs()
