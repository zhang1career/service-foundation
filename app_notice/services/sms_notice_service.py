import logging

from common.services.http import HttpCallError, HttpClientPool, request_sync
from common.utils.django_util import setting_str

logger = logging.getLogger(__name__)


class SmsNoticeService:
    @staticmethod
    def send(phone: str, content: str) -> bool:
        if not phone:
            raise ValueError("Phone is required")
        if not content:
            raise ValueError("SMS content is required")

        provider = setting_str("SMS_PROVIDER", "").lower()
        if not provider:
            raise ValueError("SMS_PROVIDER is not configured")

        if provider == "mock":
            logger.info("[SmsNoticeService.send] mock provider sent to=%s", phone)
            return True

        if provider == "http":
            endpoint = setting_str("SMS_HTTP_ENDPOINT", "")
            api_key = setting_str("SMS_HTTP_API_KEY", "")
            if not endpoint:
                raise ValueError("SMS_HTTP_ENDPOINT is required when SMS_PROVIDER=http")
            payload = {"phone": phone, "content": content}
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            try:
                response = request_sync(
                    method="POST",
                    url=endpoint,
                    pool_name=HttpClientPool.THIRD_PARTY,
                    json_body=payload,
                    headers=headers,
                    timeout_sec=5,
                )
            except HttpCallError:
                return False
            return response.status_code == 200

        raise ValueError(f"Unsupported SMS provider: {provider}")
