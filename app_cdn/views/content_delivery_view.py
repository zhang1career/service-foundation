"""
CDN content delivery view - proxy + cache (edge caching)

Serves content via:
- Cache hit: return from app_oss (cdn-cache bucket)
- Cache miss: fetch from origin, store in cache, return to user

URL: GET /api/cdn/d/{distribution_id}/{path}
"""
import logging
from urllib.parse import unquote

from django.http import HttpResponse
from rest_framework.views import APIView

from app_cdn.config import get_app_config
from app_cdn.repos import get_distribution_by_id
from app_cdn.services.cdn_cache_service import (
    build_origin_base_url,
    fetch_from_origin,
    get_from_cache,
    put_to_cache,
)

logger = logging.getLogger(__name__)


class ContentDeliveryView(APIView):
    """
    Content delivery endpoint - proxy + cache.

    GET /api/cdn/d/{distribution_id}/{path}
    """

    def get(self, request, distribution_id: str, path: str = ""):
        """distribution_id in URL is distribution primary key id."""
        path = unquote(path or "").strip()

        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return HttpResponse("Distribution not found", status=404)

        if not dist.enabled:
            return HttpResponse("Distribution disabled", status=403)

        app_config = get_app_config()
        origin_config = dist.get_origin_config()
        origin_base = build_origin_base_url(origin_config, app_config)
        if not origin_base:
            return HttpResponse("Origin error: CDN_DEFAULT_ORIGIN_URL is empty", status=500)

        # 1. Try cache first
        cached = get_from_cache(str(dist.id), path)
        if cached:
            body = cached.get("Body", b"")
            content_type = cached.get("ContentType", "application/octet-stream")
            resp = HttpResponse(body, status=200)
            resp["Content-Type"] = content_type
            resp["Content-Length"] = str(len(body))
            if cached.get("ETag"):
                resp["ETag"] = f'"{cached["ETag"]}"'
            if cached.get("LastModified"):
                lm = cached["LastModified"]
                if hasattr(lm, "strftime"):
                    resp["Last-Modified"] = lm.strftime("%a, %d %b %Y %H:%M:%S GMT")
            resp["X-Cache"] = "HIT"
            return resp

        # 2. Fetch from origin
        path_for_origin = path if path.startswith("/") else "/" + path
        origin_bucket = app_config.get("origin_default_bucket", "")
        body, content_type, status, origin_url = fetch_from_origin(
            origin_base, path_for_origin, origin_path_prefix=origin_bucket
        )
        if body is None:
            msg = f"Origin error (status={status or 502})"
            if origin_url:
                msg += f". URL: {origin_url}"
                logger.warning("[ContentDelivery] %s path=%s bucket=%s", msg, path, origin_bucket)
            return HttpResponse(msg, status=status or 502)

        # 3. Store in cache (async would be better, but sync for simplicity)
        put_to_cache(str(dist.id), path, body, content_type or "application/octet-stream")

        # 4. Return to user
        resp = HttpResponse(body, status=200)
        resp["Content-Type"] = content_type or "application/octet-stream"
        resp["Content-Length"] = str(len(body))
        resp["X-Cache"] = "MISS"
        return resp
