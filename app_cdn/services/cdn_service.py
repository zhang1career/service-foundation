"""
CDN service - CloudFront-compatible business logic

Implements CdnProviderProtocol. Handles model-to-CloudFront DTO conversion.
"""
import logging
from typing import Any, Dict, List, Optional

from app_cdn.enums.distribution_status_enum import DistributionStatusEnum
from app_cdn.enums.invalidation_status_enum import InvalidationStatusEnum
from app_cdn.exceptions.not_found_exception import (
    DistributionNotFoundException,
)
from app_cdn.repos import (
    create_distribution,
    create_invalidation,
    delete_distribution,
    get_distribution_by_id,
    get_invalidation_by_ids,
    list_distributions,
    list_invalidations,
    update_distribution,
)
from common.components.singleton import Singleton

logger = logging.getLogger(__name__)


def _origins_for_summary(dist) -> Dict[str, Any]:
    """Origins block from origin_config (source of truth). Not duplicated from domain_name."""
    oc = dist.get_origin_config()
    origins = oc.get("Origins") or {}
    items = origins.get("Items") or []
    if not items:
        return {"Quantity": 0, "Items": None}
    return {
        "Quantity": origins.get("Quantity", len(items)),
        "Items": items,
    }


def _default_cache_behavior_for_summary(dist) -> Dict[str, Any]:
    oc = dist.get_origin_config()
    dcb = oc.get("DefaultCacheBehavior")
    if isinstance(dcb, dict) and dcb:
        return dcb
    return {"TargetOriginId": "default"}


def _distribution_to_summary(dist) -> Dict[str, Any]:
    """Convert Distribution model to CloudFront DistributionSummary.

    DomainName = distribution edge hostname (column domain_name).
    Origins = from origin_config only (backend hosts differ from edge DomainName).
    """
    id_str = str(dist.id)
    return {
        "Id": id_str,
        "ARN": dist.arn or f"arn:aws:cloudfront::local:distribution/{id_str}",
        "Status": DistributionStatusEnum.to_label(dist.status),
        "DomainName": dist.domain_name,
        "Aliases": {
            "Quantity": len(dist.get_aliases_list()),
            "Items": dist.get_aliases_list() or None,
        },
        "Origins": _origins_for_summary(dist),
        "DefaultCacheBehavior": _default_cache_behavior_for_summary(dist),
        "Comment": dist.comment,
        "Enabled": dist.enabled,
    }


def _distribution_to_config(dist) -> Dict[str, Any]:
    """Convert Distribution model to DistributionConfig (for update)."""
    origin_config = dist.get_origin_config()
    out: Dict[str, Any] = {
        "CallerReference": str(dist.id),
        "Origins": origin_config.get("Origins", {"Items": [], "Quantity": 0}),
        "DefaultCacheBehavior": origin_config.get(
            "DefaultCacheBehavior", {"TargetOriginId": "default"}
        ),
        "Comment": dist.comment,
        "Enabled": dist.enabled,
        "Aliases": {
            "Quantity": len(dist.get_aliases_list()),
            "Items": dist.get_aliases_list() or None,
        },
        "OriginBucket": origin_config.get("OriginBucket") or "",
    }
    return out


class CdnService(Singleton):
    """
    CDN service implementing CloudFront-compatible interface.
    """

    def list_distributions(
            self,
            marker: Optional[str] = None,
            max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List distributions with pagination. CloudFront-compatible response."""
        max_items = max_items or 100
        result = list_distributions(marker=marker, max_items=max_items)

        items = [_distribution_to_summary(d) for d in result["Items"]]
        return {
            "DistributionList": {
                "IsTruncated": result["IsTruncated"],
                "Marker": marker or "",
                "NextMarker": result["NextMarker"] or "",
                "MaxItems": max_items,
                "Quantity": result["Quantity"],
                "Items": items if items else None,
            }
        }

    def get_distribution(self, distribution_id) -> Optional[Dict[str, Any]]:
        """Get distribution by ID."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return None
        return self._distribution_to_full(dist)

    def get_distribution_config(
            self, distribution_id
    ) -> Optional[Dict[str, Any]]:
        """Get distribution configuration (for updates)."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return None
        return _distribution_to_config(dist)

    def create_distribution(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new distribution. Origins must be provided in config."""
        caller_ref = config.get("CallerReference") or ""
        if not caller_ref:
            raise ValueError("CallerReference is required")

        origins = config.get("Origins", {})
        origin_items = origins.get("Items", []) or []
        if not origin_items:
            raise ValueError(
                "Origins.Items is required; origin URL is stored in origin_config, "
                "no longer from CDN_DEFAULT_ORIGIN_URL"
            )

        default_origin_id = origin_items[0].get("Id", "default")
        default_cache = config.get("DefaultCacheBehavior", {})
        if not isinstance(default_cache, dict):
            default_cache = {}
        default_cache = dict(default_cache)
        default_cache["TargetOriginId"] = default_origin_id

        # OriginPath 应为 OSS 路径 /api/oss，去掉错误的多余 /cdn 后缀
        normalized_items = []
        for o in origin_items:
            o = dict(o)
            path = (o.get("OriginPath") or "").strip()
            if path.endswith("/cdn"):
                o["OriginPath"] = path[:-4] or "/"
            normalized_items.append(o)

        origin_config = {
            "Origins": {"Items": normalized_items, "Quantity": len(normalized_items)},
            "DefaultCacheBehavior": default_cache,
            "Comment": config.get("Comment", ""),
            "Enabled": config.get("Enabled", True),
        }
        if "OriginBucket" in config:
            origin_config["OriginBucket"] = (config.get("OriginBucket") or "").strip()

        aliases = config.get("Aliases", {})
        alias_list = aliases.get("Items", []) if isinstance(aliases, dict) else []

        domain_name = (config.get("DomainName") or "").strip()
        if not domain_name:
            raise ValueError("DomainName is required (distribution edge hostname, e.g. localhost:8000)")

        dist = create_distribution(
            domain_name=domain_name,
            origin_config=origin_config,
            aliases=alias_list,
            enabled=config.get("Enabled", True),
            comment=config.get("Comment", ""),
        )
        # Set domain after we have id
        if dist.domain_name == "cdn.local":
            dist.domain_name = f"{dist.id}.cdn.local"
            dist.save(using="cdn_rw")

        return {"Distribution": self._distribution_to_full(dist)}

    def update_distribution(
            self,
            distribution_id,
            config: Dict[str, Any],
            if_match: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update distribution configuration."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return None
        if if_match and dist.etag != if_match:
            raise ValueError("PreconditionFailed: ETag mismatch")

        origin_config = dist.get_origin_config()
        if "Origins" in config:
            origins = config["Origins"]
            items = (origins.get("Items") or []) if isinstance(origins, dict) else []
            normalized = []
            for o in items:
                o = dict(o)
                path = (o.get("OriginPath") or "").strip()
                if path.endswith("/cdn"):
                    o["OriginPath"] = path[:-4] or "/"
                normalized.append(o)
            origin_config["Origins"] = {
                "Items": normalized,
                "Quantity": len(normalized),
            }
        if "DefaultCacheBehavior" in config:
            origin_config["DefaultCacheBehavior"] = config["DefaultCacheBehavior"]
        if "Comment" in config:
            origin_config["Comment"] = config["Comment"]
        if "OriginBucket" in config:
            origin_config["OriginBucket"] = (config.get("OriginBucket") or "").strip()

        aliases = config.get("Aliases", {})
        alias_list = aliases.get("Items", []) if isinstance(aliases, dict) else []

        updated = update_distribution(
            distribution_id=distribution_id,
            origin_config=origin_config,
            aliases=alias_list if alias_list else None,
            enabled=config.get("Enabled"),
            comment=config.get("Comment"),
        )
        return {"Distribution": self._distribution_to_full(updated)} if updated else None

    def delete_distribution(
            self, distribution_id, if_match: Optional[str] = None
    ) -> bool:
        """Delete distribution."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            return False
        if if_match and dist.etag != if_match:
            raise ValueError("PreconditionFailed: ETag mismatch")
        return delete_distribution(distribution_id)

    def create_invalidation(
            self, distribution_id, paths: List[str], caller_reference: str
    ) -> Dict[str, Any]:
        """Create cache invalidation and purge matching entries from app_oss cache."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            raise DistributionNotFoundException(str(distribution_id))

        inv = create_invalidation(
            distribution_id=distribution_id,
            paths=paths,
            caller_reference=caller_reference,
        )

        # Purge cache in app_oss for invalidation paths
        try:
            from app_cdn.services.cdn_cache_service import purge_cache_by_paths

            purged = purge_cache_by_paths(distribution_id, paths)
            if purged:
                logger.info(
                    "[create_invalidation] Purged %d cache entries for distribution id=%s",
                    purged,
                    distribution_id,
                )
        except Exception as e:
            logger.warning("[create_invalidation] Cache purge failed: %s", e)

        return {"Invalidation": self._invalidation_to_dict(inv)}

    def list_invalidations(
            self,
            distribution_id,
            marker: Optional[str] = None,
            max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List invalidations for a distribution."""
        dist = get_distribution_by_id(distribution_id)
        if not dist:
            raise DistributionNotFoundException(str(distribution_id))

        max_items = max_items or 100
        result = list_invalidations(
            distribution_id=distribution_id,
            marker=marker,
            max_items=max_items,
        )

        items = [self._invalidation_to_summary(i) for i in result["Items"]]
        return {
            "InvalidationList": {
                "IsTruncated": result["IsTruncated"],
                "Marker": marker or "",
                "NextMarker": result["NextMarker"] or "",
                "MaxItems": max_items,
                "Quantity": result["Quantity"],
                "Items": items if items else None,
            }
        }

    def get_invalidation(
            self, distribution_id, invalidation_id
    ) -> Optional[Dict[str, Any]]:
        """Get invalidation by ID."""
        inv = get_invalidation_by_ids(distribution_id, invalidation_id)
        if not inv:
            return None
        return {"Invalidation": self._invalidation_to_dict(inv)}

    def _distribution_to_full(self, dist) -> Dict[str, Any]:
        """Convert Distribution model to full CloudFront Distribution."""
        summary = _distribution_to_summary(dist)
        return {
            **summary,
            "ETag": dist.etag,
            "LastModified": self._ms_to_iso8601(dist.ut),
        }

    def _invalidation_to_summary(self, inv) -> Dict[str, Any]:
        """Convert Invalidation model to summary."""
        return {
            "Id": str(inv.id),
            "Status": InvalidationStatusEnum.to_label(inv.status),
            "CreateTime": self._ms_to_iso8601(inv.ct),
        }

    def _invalidation_to_dict(self, inv) -> Dict[str, Any]:
        """Convert Invalidation model to full Invalidation."""
        return {
            "Id": str(inv.id),
            "Status": InvalidationStatusEnum.to_label(inv.status),
            "CreateTime": self._ms_to_iso8601(inv.ct),
            "InvalidationBatch": {
                "CallerReference": inv.caller_reference,
                "Paths": {
                    "Quantity": len(inv.get_paths_list()),
                    "Items": inv.get_paths_list() or None,
                },
            },
        }

    @staticmethod
    def _ms_to_iso8601(ms: int) -> str:
        """Convert milliseconds timestamp to ISO 8601 string."""
        from datetime import datetime, timezone

        if not ms:
            return datetime.now(timezone.utc).isoformat()
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
