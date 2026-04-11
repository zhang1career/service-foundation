"""app_snowflake test setup (pytest without pytest-django).

Neuters `transaction.atomic` on `create_or_update_recount` so service tests need no DB.
"""

import importlib
from unittest.mock import patch

_snowflake_recounter_tx_neutered = False


def _neutered_atomic(*_args, **_kwargs):
    def _decorator(func):
        return func

    return _decorator


def neuter_snowflake_recounter_transaction_for_tests() -> None:
    """Idempotent; safe for pytest (pytest_configure) and manage.py test (import-time)."""
    global _snowflake_recounter_tx_neutered
    if _snowflake_recounter_tx_neutered:
        return
    patcher = patch("django.db.transaction.atomic", _neutered_atomic)
    patcher.start()
    import app_snowflake.services.recounter_service as rec_svc
    import app_snowflake.services.snowflake_generator as sf_gen

    importlib.reload(rec_svc)
    importlib.reload(sf_gen)
    patcher.stop()
    _snowflake_recounter_tx_neutered = True


def pytest_configure(config):
    neuter_snowflake_recounter_transaction_for_tests()
