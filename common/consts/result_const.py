"""
Maps business ``result_id`` to module/callable used by :mod:`common.services.result_service`.

Populate from application code or data migrations; only pairs listed here may be invoked by
:func:`common.services.result_service.get_result`.
"""

RESULT_INDEX_MAP: dict = {}
