"""
Graphiti HTTP client for app_know.
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

import requests

from service_foundation import settings

logger = logging.getLogger(__name__)


class GraphitiClient:
    """Thin HTTP wrapper around local Graphiti service."""

    def __init__(self, base_url: Optional[str] = None, timeout_sec: float = 10.0):
        self.base_url = (base_url or settings.GRAPHITI_SERVICE_URL or "").rstrip("/")
        self.timeout_sec = timeout_sec
        if not self.base_url:
            raise RuntimeError("GRAPHITI_SERVICE_URL is empty")

    def _url(self, path: str) -> str:
        p = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{p}"

    def _post(self, path: str, payload: Dict[str, Any], expected_codes: tuple[int, ...] = (200,)) -> Any:
        resp = requests.post(self._url(path), json=payload, timeout=self.timeout_sec)
        if resp.status_code not in expected_codes:
            text = resp.text[:500]
            raise RuntimeError(f"Graphiti POST {path} failed: {resp.status_code} {text}")
        if not resp.text:
            return {}
        return resp.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = requests.get(self._url(path), params=params or {}, timeout=self.timeout_sec)
        if resp.status_code != 200:
            text = resp.text[:500]
            raise RuntimeError(f"Graphiti GET {path} failed: {resp.status_code} {text}")
        if not resp.text:
            return {}
        return resp.json()

    def healthcheck(self) -> Dict[str, Any]:
        out = self._get("/healthcheck")
        return out if isinstance(out, dict) else {"ok": bool(out)}

    def add_messages(self, group_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "group_id": group_id,
            "messages": messages,
        }
        out = self._post("/messages", payload, expected_codes=(200, 202))
        return out if isinstance(out, dict) else {"data": out}

    def search(self, query: str, max_facts: int = 10, group_ids: Optional[List[str]] = None) -> Any:
        payload: Dict[str, Any] = {"query": query, "max_facts": max_facts}
        if group_ids:
            payload["group_ids"] = group_ids
        return self._post("/search", payload)

    def get_memory(
        self,
        group_id: str,
        messages: List[Dict[str, Any]],
        center_node_uuid: Optional[str] = None,
        max_facts: int = 10,
    ) -> Any:
        payload = {
            "group_id": group_id,
            "center_node_uuid": center_node_uuid,
            "messages": messages,
            "max_facts": max_facts,
        }
        return self._post("/get-memory", payload)

    def get_episodes(self, group_id: str, last_n: int = 20) -> Any:
        return self._get(f"/episodes/{group_id}", params={"last_n": last_n})


def build_message(content: str, role_type: str = "user", role: Optional[str] = "user") -> Dict[str, Any]:
    """Build Graphiti message payload with required timestamp."""
    return {
        "content": content,
        "role_type": role_type,
        "role": role,
        "timestamp": datetime.now(UTC).isoformat(),
    }
