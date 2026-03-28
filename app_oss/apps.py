from django.apps import AppConfig


class OssConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_oss"
    label = "app_oss"

    def ready(self) -> None:
        import app_oss.dict_registration  # noqa: F401
