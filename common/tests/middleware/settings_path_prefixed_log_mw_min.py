"""Minimal settings for path-prefixed request log middleware tests (no MySQL, no project LOG_DIR)."""

SECRET_KEY = "path-prefixed-log-mw-test-secret-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
]
MIDDLEWARE: list[str] = []
ROOT_URLCONF = "common.tests.middleware.urls_path_prefixed_log_mw_min"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
XXL_JOB_TOKEN = "ref-token"
XXL_JOB_ADMIN_ADDRESS = ""
PATH_PREFIXED_REQUEST_LOG = [("/api/tcc/", "test_path_prefixed_log.access")]
REST_FRAMEWORK: dict = {}
LOGGING_CONFIG = None
