"""Fusio / Paganini-style ``://{{key}}`` URL resolution (Redis registry, no local cache)."""

from __future__ import annotations

from common.services.service_discovery.expand import (
    expand_service_discovery_url,
    reset_service_discovery_redis_client_for_tests,
)

__all__ = [
    "expand_service_discovery_url",
    "reset_service_discovery_redis_client_for_tests",
]
