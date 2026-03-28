from django.apps import AppConfig


class AibrokerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_aibroker"
    label = "app_aibroker"

    def ready(self) -> None:
        import app_aibroker.dict_registration  # noqa: F401
