from __future__ import annotations

import json
import logging
from typing import Any

from common.components.singleton import Singleton
from common.enums.aigc_invoke_op_enum import AigcInvokeOp
from common.services.http import HttpCallError, request_sync
from common.utils.django_util import effective_setting_str
from common.utils.http_util import http_origin_url, normalize_http_path, parse_http_target

logger = logging.getLogger(__name__)

_AIGC_HTTP_POOL = "aigc_upstream_pool"
_AIGC_TIMEOUT_SEC = 120.0


class AigcAPI(Singleton):
    """POST JSON to an OpenAI-compatible upstream. *params* is the full body except ``model`` (injected here)."""

    def __init__(
            self,
            base_url: str | None = None,
            api_key: str | None = None,
    ):
        base_url = effective_setting_str(base_url, "AIGC_API_URL")
        api_key = effective_setting_str(api_key, "AIGC_API_KEY")
        if not base_url or not api_key:
            raise RuntimeError(
                "base URL and API key are required "
                "(set provider base_url/api_key or AIGC_API_URL and AIGC_API_KEY)"
            )
        host, port, tls = parse_http_target(base_url)
        self._origin = http_origin_url(host, port, tls)
        self._api_key = api_key

    def invoke(
            self,
            path: str,
            op: AigcInvokeOp,
            model: str,
            params: dict[str, Any],
    ) -> str | list[float] | dict[str, Any] | None:
        """*params*: request body without ``model``; *model* is merged in before POST."""
        try:
            if op == AigcInvokeOp.CHAT:
                return self._invoke_chat(path, model, params)
            if op == AigcInvokeOp.IMAGE:
                return self._invoke_image(path, model, params)
            if op == AigcInvokeOp.VIDEO:
                return self._invoke_video(path, model, params)
            if op == AigcInvokeOp.EMBEDDING:
                return self._invoke_embedding(path, model, params)
            raise RuntimeError(f"unsupported invoke op: {op!r}")
        except Exception:
            logger.exception("[aigc] invoke %s failed", op)
            raise

    def _invoke_chat(
            self,
            path: str,
            model: str,
            params: dict[str, Any],
    ) -> str | None:
        body = dict(params)
        body["model"] = model
        data = self._post(path, body)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        msg = first.get("message")
        if isinstance(msg, dict):
            out = msg.get("content")
            return out if isinstance(out, str) else None
        return None

    def _invoke_image(
            self,
            path: str,
            model: str,
            params: dict[str, Any],
    ) -> dict[str, Any]:
        body = dict(params)
        body["model"] = model
        return self._post(path, body)

    def _invoke_video(
            self,
            path: str,
            model: str,
            params: dict[str, Any],
    ) -> dict[str, Any]:
        body = dict(params)
        body["model"] = model
        return self._post(path, body)

    def _invoke_embedding(
            self,
            path: str,
            model: str,
            params: dict[str, Any],
    ) -> list[float]:
        body = dict(params)
        body["model"] = model
        data = self._post(path, body)
        arr = data.get("data")
        if not isinstance(arr, list) or not arr:
            raise RuntimeError("empty embedding response")
        row0 = arr[0]
        if not isinstance(row0, dict):
            raise RuntimeError("empty embedding response")
        emb = row0.get("embedding")
        if not isinstance(emb, list):
            raise RuntimeError("empty embedding response")
        return [float(x) for x in emb]

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(method="POST", path=path, body=body)

    def request_json(
            self,
            *,
            method: str,
            path: str,
            body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path_n = normalize_http_path(path)
        url = self._origin + path_n
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            res = request_sync(
                method=(method or "").strip().upper(),
                url=url,
                pool_name=_AIGC_HTTP_POOL,
                headers=headers,
                data=payload,
                timeout_sec=_AIGC_TIMEOUT_SEC,
            )
        except HttpCallError as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e
        raw = res.content
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        if res.status_code >= 400:
            err = data.get("error")
            msg = err if isinstance(err, str) else (
                (err or {}).get("message") if isinstance(err, dict) else None
            )
            msg = msg or raw.decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"HTTP {res.status_code}: {msg}")
        return data
