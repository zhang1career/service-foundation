from django.conf import settings

from common.services.http import HttpCallError, request_sync


class BaseHttpAdapter:
    adapter_name = "adapter"

    def __init__(self, *, base_url, api_key="", auth_mode="bearer"):
        self._base_url = str(base_url or "").rstrip("/")
        self._api_key = str(api_key or "").strip()
        self._auth_mode = auth_mode
        if not self._base_url:
            raise ValueError(f"{self.adapter_name} base url is required")

    def _headers(self):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            if self._auth_mode == "api-key":
                headers["api-key"] = self._api_key
            elif self._auth_mode == "opensearch":
                headers["Authorization"] = f"ApiKey {self._api_key}"
            else:
                headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _request(self, *, method, path, json_body=None, data=None):
        url = f"{self._base_url}{path}"
        try:
            response = request_sync(
                method=method,
                url=url,
                headers=self._headers(),
                json_body=json_body,
                data=data,
                timeout_sec=float(getattr(settings, "SEARCHREC_HTTP_TIMEOUT", 3.0)),
            )
        except HttpCallError as exc:
            raise RuntimeError(f"{self.adapter_name} request failed: {exc}") from exc
        if response.status_code >= 300:
            raise RuntimeError(f"{self.adapter_name} status={response.status_code}, body={response.text}")
        return response
