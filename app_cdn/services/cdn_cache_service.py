"""
CDN cache service - edge caching backed by app_oss

Provides:
- Cache read/write (stored in app_oss bucket)
- Origin fetch (proxy)
- Cache invalidation (purge on CreateInvalidation)
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from app_cdn.config import get_app_config
from common.services.http import HttpCallError, HttpClientPool, request_sync

logger = logging.getLogger(__name__)


def _get_oss_client():
    """Lazy import OSSClient - app_oss may not be enabled."""
    from django.conf import settings

    if not getattr(settings, "APP_OSS_ENABLED", False):
        return None
    try:
        from app_oss.exceptions.object_not_found_exception import ObjectNotFoundException
        from app_oss.services.oss_client import OSSClient

        return OSSClient(), ObjectNotFoundException
    except Exception as e:
        logger.warning("[CdnCacheService] OSS not available: %s", e)
        return None


def _normalize_path(path: str) -> str:
    """Normalize path: remove leading slash, empty -> ''."""
    p = (path or "").strip().lstrip("/")
    return p or ""


def _cache_key(distribution_id: str, path: str) -> str:
    """Cache key in OSS: {distribution_id}/{path}."""
    norm = _normalize_path(path)
    if not norm:
        return f"{distribution_id}/index.html"
    return f"{distribution_id}/{norm}"


def get_from_cache(distribution_id: str, path: str) -> Optional[Dict[str, Any]]:
    """
    Get object from CDN cache (app_oss).

    Returns:
        Dict with Body, ContentType, ContentLength, ETag, etc. or None if miss.
    """
    oss_result = _get_oss_client()
    if not oss_result:
        return None
    client, ObjectNotFoundException = oss_result
    config = get_app_config()
    bucket = config.get("cdn_cache_bucket", "cdn-cache")
    key = _cache_key(distribution_id, path)
    try:
        storage = client.get_local_storage()
        obj = storage.get_object(bucket_name=bucket, object_key=key)
        return obj
    except ObjectNotFoundException:
        return None
    except Exception as e:
        logger.warning("[get_from_cache] Error: %s", e)
        return None


def put_to_cache(
    distribution_id: str,
    path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> bool:
    """Store object in CDN cache. Returns True on success."""
    oss_result = _get_oss_client()
    if not oss_result:
        return False
    client, _ = oss_result
    config = get_app_config()
    bucket = config.get("cdn_cache_bucket", "cdn-cache")
    key = _cache_key(distribution_id, path)
    try:
        storage = client.get_local_storage()
        storage.put_object(
            bucket_name=bucket,
            object_key=key,
            data=data,
            content_type=content_type,
        )
        logger.debug("[put_to_cache] Cached %s/%s", distribution_id, path)
        return True
    except Exception as e:
        logger.warning("[put_to_cache] Error: %s", e)
        return False


def build_origin_base_url(origin_config: dict) -> str:
    """
    Build origin base URL from distribution origin_config.

    Reads Origins.Items and DefaultCacheBehavior.TargetOriginId.
    OriginPath: strips erroneous trailing /cdn suffix (OSS path should be /api/oss, not /api/oss/cdn).
    """
    origins = origin_config.get("Origins", {}) or {}
    items = origins.get("Items", []) or []
    if not items:
        return ""

    target_id = (
        origin_config.get("DefaultCacheBehavior", {}) or {}
    ).get("TargetOriginId", "default")
    origin = next((o for o in items if o.get("Id") == target_id), items[0])

    domain = (origin.get("DomainName") or "").strip()
    if not domain:
        return ""

    custom = origin.get("CustomOriginConfig", {}) or {}
    policy = (custom.get("OriginProtocolPolicy") or "http-only").lower()
    scheme = "https" if "https" in policy else "http"

    origin_path = (origin.get("OriginPath") or "").strip()
    # OriginPath 应为 OSS 路径如 /api/oss，错误的多余 /cdn 后缀需去掉
    if origin_path.endswith("/cdn"):
        origin_path = origin_path[:-4] or "/"
    if origin_path and not origin_path.startswith("/"):
        origin_path = "/" + origin_path

    return f"{scheme}://{domain}{origin_path}".rstrip("/")


def get_origin_bucket(origin_config: dict) -> str:
    """
    OSS path prefix (bucket name) for this distribution, from origin_config.

    Extension field (not AWS CloudFront): OriginBucket.
    """
    v = origin_config.get("OriginBucket")
    if v is None:
        return ""
    return str(v).strip()


def fetch_from_origin(
    origin_base_url: str,
    path: str,
    origin_path_prefix: str = "",
) -> Tuple[Optional[bytes], Optional[str], int, Optional[str]]:
    """
    Fetch content from origin via HTTP GET.

    Args:
        origin_base_url: Base URL of origin (e.g. http://localhost:8000/api/oss)
        path: Request path (e.g. /images/photo.jpg)
        origin_path_prefix: Optional prefix for path (e.g. mybucket for OSS bucket)

    Returns:
        (body_bytes, content_type, status_code, request_url)
        (None, None, status_code, url) on error.
    """
    path = path if path.startswith("/") else "/" + path
    if origin_path_prefix:
        prefix = origin_path_prefix.rstrip("/")
        path = "/" + prefix + path
    url = origin_base_url.rstrip("/") + path
    try:
        resp = request_sync(
            method="GET",
            url=url,
            pool_name=HttpClientPool.THIRD_PARTY,
            timeout_sec=30,
        )
        if resp.status_code != 200:
            logger.warning("[fetch_from_origin] %s -> %d", url, resp.status_code)
            return None, None, resp.status_code, url
        ct = resp.headers.get("Content-Type", "application/octet-stream")
        return resp.content, ct, 200, url
    except HttpCallError as e:
        logger.exception("[fetch_from_origin] Error: %s", e)
        return None, None, 502, url


def purge_cache_by_paths(distribution_id: str, paths: List[str]) -> int:
    """
    Purge cache entries matching invalidation paths.
    Paths support wildcard: /images/* -> delete all under images/

    Returns:
        Number of objects deleted.
    """
    oss_result = _get_oss_client()
    if not oss_result:
        return 0
    client, ObjectNotFoundException = oss_result
    config = get_app_config()
    bucket = config.get("cdn_cache_bucket", "cdn-cache")
    storage = client.get_local_storage()
    deleted = 0

    for pattern in paths:
        pattern = pattern.strip()
        if not pattern:
            continue
        # Convert CloudFront path to prefix: /images/* -> images/
        # /* -> all under distribution
        if pattern == "/*" or pattern == "*":
            prefix = f"{distribution_id}/"
        elif pattern.endswith("/*"):
            prefix = f"{distribution_id}/{pattern[:-2].lstrip('/')}/"
        else:
            # Exact path
            prefix = f"{distribution_id}/{pattern.lstrip('/')}"

        try:
            result = storage.list_objects_v2(
                bucket_name=bucket,
                prefix=prefix,
                max_keys=1000,
            )
            contents = result.get("Contents", [])
            for obj in contents:
                key = obj.get("Key")
                if not key:
                    continue
                try:
                    storage.delete_object(bucket_name=bucket, object_key=key)
                    deleted += 1
                except Exception as e:
                    logger.warning("[purge_cache] Failed to delete %s: %s", key, e)

            # Handle pagination if truncated
            while result.get("IsTruncated") and result.get("NextContinuationToken"):
                result = storage.list_objects_v2(
                    bucket_name=bucket,
                    prefix=prefix,
                    max_keys=1000,
                    continuation_token=result["NextContinuationToken"],
                )
                for obj in result.get("Contents", []):
                    key = obj.get("Key")
                    if key:
                        try:
                            storage.delete_object(bucket_name=bucket, object_key=key)
                            deleted += 1
                        except Exception as e:
                            logger.warning("[purge_cache] Failed to delete %s: %s", key, e)
        except Exception as e:
            logger.warning("[purge_cache] Error for prefix %s: %s", prefix, e)

    if deleted:
        logger.info("[purge_cache] Deleted %d objects for distribution %s", deleted, distribution_id)
    return deleted
