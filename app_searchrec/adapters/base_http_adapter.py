from django.conf import settings

from common.services.http import HttpCallError, request_sync
from common.utils.http_auth_util import build_auth_headers


class BaseHttpAdapter:
    adapter_name = "adapter"

    def __init__(self, *, base_url, api_key="", auth_mode="bearer"):
        self._base_url = str(base_url or "").rstrip("/")
        self._api_key = str(api_key or "").strip()
        self._auth_mode = auth_mode
        if not self._base_url:
            raise ValueError(f"{self.adapter_name} base url is required")

    def _headers(self):
        return build_auth_headers(api_key=self._api_key, auth_mode=self._auth_mode)

    def _request_raw(self, *, method, path, json_body=None, data=None):
        url = f"{self._base_url}{path}"
        try:
            return request_sync(
                method=method,
                url=url,
                headers=self._headers(),
                json_body=json_body,
                data=data,
                timeout_sec=float(settings.SEARCHREC_HTTP_TIMEOUT),
            )
        except HttpCallError as exc:
            raise RuntimeError(f"{self.adapter_name} request failed: {exc}") from exc

    def _request(self, *, method, path, json_body=None, data=None):
        response = self._request_raw(method=method, path=path, json_body=json_body, data=data)
        if response.status_code >= 300:
            raise RuntimeError(f"{self.adapter_name} status={response.status_code}, body={response.text}")
        return response
