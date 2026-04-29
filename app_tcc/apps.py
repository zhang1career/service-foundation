from django.apps import AppConfig


class AppTccConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_tcc"
    label = "app_tcc"
    verbose_name = "TCC"

    def ready(self) -> None:
        import app_tcc.dict_registration  # noqa: F401

        from app_tcc.services import xxl_job_handlers

        xxl_job_handlers.register_tcc_jobs()
