"""Minimal settings for XXL executor/middleware contract tests (no MySQL, no project LOG_DIR)."""

SECRET_KEY = "xxl-mw-test-secret-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
]
MIDDLEWARE: list[str] = []
ROOT_URLCONF = "common.tests.middleware.urls_xxl_mw_min"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
XXL_JOB_TOKEN = "ref-token"
XXL_JOB_ADMIN_ADDRESS = ""
XXLJOB_EXECUTOR_ACCESS_LOG = [("/api/tcc/", "test_xxl_mw.access")]
REST_FRAMEWORK: dict = {}
LOGGING_CONFIG = None
