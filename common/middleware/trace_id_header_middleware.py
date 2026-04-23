"""
Normalize incoming trace headers so log_request_id sees a single META key.

Django exposes ``X-Request-Id`` as ``HTTP_X_REQUEST_ID`` and ``X-Trace-Id`` as
``HTTP_X_TRACE_ID``. RequestIDMiddleware reads only ``LOG_REQUEST_ID_HEADER``.
If the client sends only ``X-Trace-Id``, copy it to ``HTTP_X_REQUEST_ID`` when
the latter is absent.
"""

from django.utils.deprecation import MiddlewareMixin


class TraceIdHeaderNormalizeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.META.get("HTTP_X_REQUEST_ID"):
            return None
        tid = request.META.get("HTTP_X_TRACE_ID")
        if tid:
            request.META["HTTP_X_REQUEST_ID"] = tid
        return None
