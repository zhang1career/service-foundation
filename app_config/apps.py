from django.apps import AppConfig


class ConfigAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_config"
    verbose_name = "配置中心"

    def ready(self) -> None:
        import app_config.dict_registration  # noqa: F401
