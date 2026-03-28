from django.apps import AppConfig


class KnowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_know"
    label = "app_know"

    def ready(self) -> None:
        import app_know.dict_registration  # noqa: F401
