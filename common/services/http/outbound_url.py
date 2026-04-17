"""
Outbound HTTP URL policy (SSRF mitigation) for :func:`common.services.http.executor.request_sync`.

Validates scheme and host before a request is issued. Hostnames are resolved and each
returned address is checked (private, loopback, link-local, multicast, reserved).
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse, urlunparse

from django.conf import settings

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Hostnames blocked without DNS (common SSRF targets and local names).
_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata.goog",
    }
)


class OutboundUrlPolicyError(ValueError):
    """Raised when a URL is rejected by outbound policy (do not retry as transport failure)."""


def sanitize_url_for_log(url: str) -> str:
    """Return scheme + netloc + path only (no userinfo, query, or fragment)."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def validate_outbound_http_url(url: str) -> None:
    """
    Reject URLs that are not safe for server-side outbound HTTP(S) fetches.

    - Only ``http`` and ``https`` schemes.
    - No userinfo (embedded credentials).
    - Literal IPv4/IPv6 addresses must not be private, loopback, link-local, etc.
    - Hostnames must not be in the static blocklist; when DNS resolution is enabled,
      all resolved addresses must pass the same IP checks.
    """
    if not url or not isinstance(url, str):
        raise OutboundUrlPolicyError("url must be a non-empty string")

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise OutboundUrlPolicyError("only http and https URLs are allowed")

    host = parsed.hostname
    if not host:
        raise OutboundUrlPolicyError("url has no host")

    if parsed.username is not None or parsed.password is not None:
        raise OutboundUrlPolicyError("userinfo in URL is not allowed")

    if _literal_ip_check(host):
        return

    host_lower = host.lower()
    if host_lower in _BLOCKED_HOSTNAMES:
        raise OutboundUrlPolicyError("hostname is not allowed")

    if not _resolve_dns_enabled():
        raise OutboundUrlPolicyError(
            "hostname requires DNS validation; enable HTTPX_OUTBOUND_SSRF_RESOLVE_DNS"
        )

    _check_resolved_host_ips(host)


def _resolve_dns_enabled() -> bool:
    return bool(getattr(settings, "HTTPX_OUTBOUND_SSRF_RESOLVE_DNS", True))


def _literal_ip_check(host: str) -> bool:
    """
    If *host* is a literal IP, validate it and return True.
    If it is not a literal IP, return False.
    """
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    _reject_if_bad_ip(ip)
    return True


def _reject_if_bad_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise OutboundUrlPolicyError("address is not allowed for outbound HTTP")


def _check_resolved_host_ips(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        logger.info("outbound url policy: host resolution failed host=%s", hostname)
        raise OutboundUrlPolicyError("host could not be resolved") from exc

    if not infos:
        raise OutboundUrlPolicyError("host resolved to no addresses")

    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise OutboundUrlPolicyError("resolved address is not a valid IP") from None
        _reject_if_bad_ip(ip)
