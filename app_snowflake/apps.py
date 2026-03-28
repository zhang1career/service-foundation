from django.apps import AppConfig


class SnowflakeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_snowflake"
    label = "app_snowflake"

    def ready(self) -> None:
        import app_snowflake.dict_registration  # noqa: F401
