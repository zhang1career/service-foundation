"""Minimal settings for HTTP request log middleware tests (no MySQL, no project LOG_DIR)."""

SECRET_KEY = "http-request-log-mw-test-secret-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
]
MIDDLEWARE: list[str] = []
ROOT_URLCONF = "common.tests.middleware.urls_http_request_log_mw_min"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
XXL_JOB_TOKEN = "ref-token"
XXL_JOB_ADMIN_ADDRESS = ""
HTTP_REQUEST_LOG_LOGGER = "test_http_request_log.access"
REST_FRAMEWORK: dict = {}
LOGGING_CONFIG = None
