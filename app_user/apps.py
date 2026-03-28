from django.apps import AppConfig


class AppUserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_user"

    def ready(self) -> None:
        import app_user.dict_registration  # noqa: F401
