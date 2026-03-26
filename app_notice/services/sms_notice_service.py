import logging
from typing import Optional

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class SmsNoticeService:
    @staticmethod
    def send(phone: str, content: str) -> bool:
        if not phone:
            raise ValueError("Phone is required")
        if not content:
            raise ValueError("SMS content is required")

        provider = getattr(settings, "SMS_PROVIDER", "").strip().lower()
        if not provider:
            raise ValueError("SMS_PROVIDER is not configured")

        if provider == "mock":
            logger.info("[SmsNoticeService.send] mock provider sent to=%s", phone)
            return True

        if provider == "http":
            endpoint = getattr(settings, "SMS_HTTP_ENDPOINT", "").strip()
            api_key = getattr(settings, "SMS_HTTP_API_KEY", "").strip()
            if not endpoint:
                raise ValueError("SMS_HTTP_ENDPOINT is required when SMS_PROVIDER=http")
            payload = {"phone": phone, "content": content}
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            response = requests.post(endpoint, json=payload, headers=headers, timeout=5)
            return response.status_code == 200

        raise ValueError(f"Unsupported SMS provider: {provider}")
