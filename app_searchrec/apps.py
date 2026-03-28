from django.apps import AppConfig


class AppSearchRecConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_searchrec"

    def ready(self) -> None:
        import app_searchrec.dict_registration  # noqa: F401
