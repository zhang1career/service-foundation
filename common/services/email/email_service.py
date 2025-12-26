from email.mime.image import MIMEImage
from functools import lru_cache
from typing import List

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives

from common.utils.file_util import app_path


def send_email(subject: str, body: str, recipient_list: List):
    """
    send email to recipient_list
    """
    return send_mail(subject, body, settings.EMAIL_HOST_USER, recipient_list)


def send_email_multipart(subject: str, body: str, logo_path: str, recipient_list: List):
    """
    :return: number of emails have been sent
    """
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_list
    )
    message.mixed_subtype = "related"
    message.attach_alternative(body, "text/html")
    message.attach(build_logo(logo_path))
    return message.send(fail_silently=False)


@lru_cache
def build_logo(logo_path: str):
    """
    a helper function that attaches the logo
    """
    with open(app_path(logo_path), 'rb') as f:
        logo_data = f.read()
    logo = MIMEImage(logo_data)
    logo.add_header('Content-ID', '<logo>')
    return logo
