import logging
from typing import Iterable

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailNoticeService:
    @staticmethod
    def send(subject: str, body: str, recipients: Iterable[str]) -> int:
        recipient_list = [item for item in recipients if item]
        if not recipient_list:
            raise ValueError("Email recipients are required")
        if not subject:
            raise ValueError("Email subject is required")
        if body is None:
            raise ValueError("Email body is required")
        from_email = getattr(settings, "EMAIL_HOST_USER", "")
        return send_mail(subject, body, from_email, recipient_list)
