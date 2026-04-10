"""
Server-side aggregation of dependency checks for the console monitoring page.

Does not expose secrets; optional AIBroker metrics use CONSOLE_AIBROKER_ACCESS_KEY from settings only.
"""

from __future__ import annotations

import logging
import socket
import time
from typing import Any

from django.conf import settings
from django.db import connections
from django.test import RequestFactory
from django.utils import timezone

logger = logging.getLogger(__name__)

_APP_TO_DB_ALIAS: dict[str, str] = {
    "aibroker": "aibroker_rw",
    "cdn": "cdn_rw",
    "cms": "cms_rw",
    "know": "know_rw",
    "mail": "mailserver_rw",
    "notice": "notice_rw",
    "oss": "oss_rw",
    "searchrec": "searchrec_rw",
    "snowflake": "snowflake_rw",
    "user": "user_rw",
    "verify": "verify_rw",
}

_MAIL_TCP_HOST = "127.0.0.1"
_MAIL_TCP_TIMEOUT_S = 1.0


def _ms_since(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


def _ping_mysql(alias: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        conn = connections[alias]
        conn.ensure_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"ok": True, "ms": _ms_since(t0)}
    except Exception as exc:
        logger.debug("mysql ping failed alias=%s", alias, exc_info=True)
        return {"ok": False, "ms": _ms_since(t0), "error": str(exc)[:500]}


def _ping_redis_cache() -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        from django.core.cache import cache

        key = "__console_monitoring_ping__"
        cache.set(key, "1", timeout=5)
        if cache.get(key) != "1":
            return {"ok": False, "ms": _ms_since(t0), "error": "cache get/set mismatch"}
        return {"ok": True, "ms": _ms_since(t0)}
    except Exception as exc:
        logger.debug("redis cache ping failed", exc_info=True)
        return {"ok": False, "ms": _ms_since(t0), "error": str(exc)[:500]}


def _ping_neo4j() -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        from py2neo import Graph

        g = Graph(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASS),
            name=settings.NEO4J_DATABASE,
        )
        g.run("RETURN 1 AS n")
        return {"ok": True, "ms": _ms_since(t0)}
    except Exception as exc:
        logger.debug("neo4j ping failed", exc_info=True)
        return {"ok": False, "ms": _ms_since(t0), "error": str(exc)[:500]}


def _ping_mongo_atlas() -> dict[str, Any]:
    user = (getattr(settings, "MONGO_ATLAS_USER", "") or "").strip()
    password = (getattr(settings, "MONGO_ATLAS_PASS", "") or "").strip()
    if not user or not password:
        return {"ok": False, "skipped": True, "reason": "mongo credentials not configured"}

    t0 = time.perf_counter()
    client = None
    try:
        from pymongo import MongoClient
        from urllib.parse import quote_plus

        host = getattr(settings, "MONGO_ATLAS_HOST", "cluster.mongodb.net")
        cluster = getattr(settings, "MONGO_ATLAS_CLUSTER", "cluster0")
        db_name = getattr(settings, "MONGO_ATLAS_DB", "know")
        u = quote_plus(user)
        p = quote_plus(password)
        uri = f"mongodb+srv://{u}:{p}@{cluster}.{host}/?retryWrites=true&w=majority&appName=sf_monitoring"
        client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return {"ok": True, "ms": _ms_since(t0), "db": db_name}
    except Exception as exc:
        logger.debug("mongo ping failed", exc_info=True)
        return {"ok": False, "ms": _ms_since(t0), "error": str(exc)[:500]}
    finally:
        if client is not None:
            client.close()


def _tcp_port_open(host: str, port: int, timeout_s: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _probe_drf_view(view_cls, path: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        factory = RequestFactory()
        request = factory.get(path)
        response = view_cls.as_view()(request)
        ok = response.status_code == 200
        return {
            "ok": ok,
            "ms": _ms_since(t0),
            "status_code": response.status_code,
        }
    except Exception as exc:
        logger.debug("drf view probe failed path=%s", path, exc_info=True)
        return {"ok": False, "ms": _ms_since(t0), "error": str(exc)[:500]}


def _aibroker_metrics_if_configured() -> dict[str, Any] | None:
    raw_key = (getattr(settings, "CONSOLE_AIBROKER_ACCESS_KEY", "") or "").strip()
    if not raw_key:
        return None
    try:
        from app_aibroker.services.auth_service import resolve_reg
        from app_aibroker.services.metrics_service import summary_since

        reg, errmsg = resolve_reg({"access_key": raw_key}, None)
        if not reg:
            return {"error": errmsg or "invalid access_key", "configured": True}
        window_ms = int(getattr(settings, "CONSOLE_AIBROKER_METRICS_WINDOW_MS", 86400000) or 86400000)
        data = summary_since(reg_id=reg.id, window_ms=window_ms)
        return {"configured": True, "data": data}
    except Exception as exc:
        logger.debug("aibroker metrics snapshot failed", exc_info=True)
        return {"configured": True, "error": str(exc)[:500]}


def collect_monitoring_snapshot() -> dict[str, Any]:
    """Build a JSON-serializable monitoring snapshot (for template or optional JSON API)."""
    collected_at = timezone.now().isoformat()
    out: dict[str, Any] = {"collected_at": collected_at}

    out["mysql"] = {"default": _ping_mysql("default")}

    for app_key, alias in _APP_TO_DB_ALIAS.items():
        flag = f"APP_{app_key.upper()}_ENABLED"
        if app_key == "mail":
            flag = "APP_MAILSERVER_ENABLED"
        enabled = bool(getattr(settings, flag, False))
        if enabled:
            out["mysql"][alias] = _ping_mysql(alias)

    out["redis_cache"] = _ping_redis_cache()

    if getattr(settings, "APP_KNOW_ENABLED", False):
        out["neo4j"] = _ping_neo4j()
        out["mongo_atlas"] = _ping_mongo_atlas()
    else:
        out["neo4j"] = {"skipped": True, "reason": "APP_KNOW_ENABLED is False"}
        out["mongo_atlas"] = {"skipped": True, "reason": "APP_KNOW_ENABLED is False"}

    out["mail_tcp"] = {"skipped": True}
    if getattr(settings, "APP_MAILSERVER_ENABLED", False):
        out["mail_tcp"] = {
            "host": _MAIL_TCP_HOST,
            "smtp_25": _tcp_port_open(_MAIL_TCP_HOST, 25, _MAIL_TCP_TIMEOUT_S),
            "imap_143": _tcp_port_open(_MAIL_TCP_HOST, 143, _MAIL_TCP_TIMEOUT_S),
        }

    out["http_probes"] = {}
    if getattr(settings, "APP_AIBROKER_ENABLED", False):
        from app_aibroker.views.health_view import HealthView

        out["http_probes"]["aibroker_v1_health"] = _probe_drf_view(HealthView, "/api/ai/v1/health")

    if getattr(settings, "APP_SEARCHREC_ENABLED", False):
        from app_searchrec.views.searchrec_view import SearchRecHealthView

        out["http_probes"]["searchrec_health"] = _probe_drf_view(SearchRecHealthView, "/api/searchrec/health")

    out["aibroker_metrics"] = _aibroker_metrics_if_configured()

    out["searchrec_backends"] = {
        "opensearch_enabled": bool(getattr(settings, "SEARCHREC_OPENSEARCH_ENABLED", False)),
        "milvus_enabled": bool(getattr(settings, "SEARCHREC_MILVUS_ENABLED", False)),
        "qdrant_enabled": bool(getattr(settings, "SEARCHREC_QDRANT_ENABLED", False)),
        "feast_enabled": bool(getattr(settings, "SEARCHREC_FEAST_ENABLED", False)),
        "http_timeout_s": float(getattr(settings, "SEARCHREC_HTTP_TIMEOUT", 3.0)),
    }

    out["app_db_status"] = {}
    for app_key, alias in _APP_TO_DB_ALIAS.items():
        flag = f"APP_{app_key.upper()}_ENABLED"
        if app_key == "mail":
            flag = "APP_MAILSERVER_ENABLED"
        enabled = bool(getattr(settings, flag, False))
        if not enabled:
            out["app_db_status"][app_key] = {"enabled": False, "db": None}
            continue
        ping = out["mysql"].get(alias)
        if ping is None:
            ping = _ping_mysql(alias)
            out["mysql"][alias] = ping
        out["app_db_status"][app_key] = {
            "enabled": True,
            "db_alias": alias,
            "db_ok": bool(ping.get("ok")),
        }

    return out


def enrich_snapshot_for_response(raw: dict) -> dict:
    """Add data_json for AIBroker metrics when present (for JSON / client render)."""
    import json

    m = raw
    am = m.get("aibroker_metrics")
    if isinstance(am, dict) and am.get("data") is not None:
        m = dict(m)
        am = dict(am)
        am["data_json"] = json.dumps(am["data"], ensure_ascii=False, indent=2)
        m["aibroker_metrics"] = am
    return m


def get_snapshot_payload() -> dict:
    """Single entry for HTTP API and async console refresh."""
    return enrich_snapshot_for_response(collect_monitoring_snapshot())
