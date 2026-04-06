import json

from django.conf import settings

from app_user.enums.event_status_enum import EventStatusEnum
from app_user.repos import (
    create_event,
    get_event_by_id,
    update_event_after_code,
    update_event_status,
)
from common.utils.http_util import post


def create_verify_event_and_send_notice(
        *,
        biz_type: int,
        level: int,
        notice_channel: int,
        notice_target: str,
        payload_json: str,
        subject: str,
        content_template: str,
):
    """Create pending event, request verify code, enqueue notice.

    ``content_template`` is passed to ``str.format`` with ``code`` and ``event_id``.
    """
    event = create_event(
        biz_type=biz_type,
        level=level,
        notice_channel=notice_channel,
        notice_target=notice_target,
        payload_json=payload_json,
    )
    verify_access_key, notice_access_key = load_verify_notice_access_keys()
    code = request_verify_code_for_event(
        event_id=event.id,
        verify_access_key=verify_access_key,
        level=level,
    )
    enqueue_notice_for_event(
        event_id=event.id,
        notice_access_key=notice_access_key,
        channel=notice_channel,
        target=notice_target,
        subject=subject,
        content=content_template.format(code=code, event_id=event.id),
    )
    return event


def load_verify_notice_access_keys() -> tuple[str, str]:
    verify_access_key = (getattr(settings, "USER_VERIFY_ACCESS_KEY", "") or "").strip()
    notice_access_key = (getattr(settings, "USER_NOTICE_ACCESS_KEY", "") or "").strip()
    if not verify_access_key:
        raise ValueError("USER_VERIFY_ACCESS_KEY is required")
    if not notice_access_key:
        raise ValueError("USER_NOTICE_ACCESS_KEY is required")
    return verify_access_key, notice_access_key


def _verify_request_url() -> str:
    raw = getattr(settings, "VERIFY_REQUEST_URL", None)
    if raw is None or not str(raw).strip():
        raise ValueError("VERIFY_REQUEST_URL is not configured")
    return str(raw).strip()


def _verify_check_url() -> str:
    raw = getattr(settings, "VERIFY_CHECK_URL", None)
    if raw is None or not str(raw).strip():
        raise ValueError("VERIFY_CHECK_URL is not configured")
    return str(raw).strip()


def _notice_service_url() -> str:
    raw = getattr(settings, "NOTICE_SERVICE_URL", None)
    if raw is None or not str(raw).strip():
        raise ValueError("NOTICE_SERVICE_URL is not configured")
    return str(raw).strip()


def request_verify_code_for_event(
        *,
        event_id: int,
        verify_access_key: str,
        level: int,
) -> str:
    verify_resp = post(
        url=_verify_request_url(),
        data={
            "access_key": verify_access_key,
            "level": level,
            "ref_id": event_id,
        },
    )
    if not verify_resp or verify_resp.get("errorCode") != 0:
        update_event_status(
            event_id,
            status=EventStatusEnum.FAILED.value,
            message="verify request failed",
        )
        raise ValueError("failed to request verify code")
    verify_data = verify_resp.get("data") or {}
    code = verify_data.get("code")
    code_id = int(verify_data.get("code_id") or 0)
    ref_id = int(verify_data.get("ref_id") or 0)
    if not code or code_id <= 0 or ref_id != event_id:
        update_event_status(
            event_id,
            status=EventStatusEnum.FAILED.value,
            message="invalid verify response",
        )
        raise ValueError("invalid verify response")
    update_event_after_code(event_id, verify_code_id=code_id, verify_ref_id=ref_id)
    return code


def enqueue_notice_for_event(
        *,
        event_id: int,
        notice_access_key: str,
        channel,
        target: str,
        subject: str,
        content: str,
) -> None:
    notice_resp = post(
        url=_notice_service_url(),
        data={
            "access_key": notice_access_key,
            "event_id": event_id,
            "channel": channel,
            "target": target,
            "subject": subject,
            "content": content,
        },
    )
    if not notice_resp or notice_resp.get("errorCode") != 0:
        update_event_status(
            event_id,
            status=EventStatusEnum.FAILED.value,
            message="notice enqueue failed",
        )
        raise ValueError("failed to enqueue notice")


def post_verify_check(*, verify_access_key: str, code_id: int, code: str):
    return post(
        url=_verify_check_url(),
        data={
            "access_key": verify_access_key,
            "code_id": code_id,
            "code": code,
        },
    )


def verify_payload_code_for_pending_event(*, payload: dict, expected_biz_type: int):
    """Parse ``event_id`` / ``code``, load pending event for ``expected_biz_type``, verify code.

    On failed verify HTTP response, updates event message to ``waiting for verified``.

    Returns ``(event, data)`` where ``data`` is ``payload_json`` parsed as a dict.
    """
    event_id = int(payload.get("event_id") or 0)
    code = (payload.get("code") or "").strip()
    if event_id <= 0 or not code:
        raise ValueError("event_id and code are required")
    event = get_event_by_id(event_id)
    if (
        not event
        or event.biz_type != expected_biz_type
        or event.status != EventStatusEnum.PENDING_VERIFY.value
    ):
        raise ValueError("invalid event")
    verify_access_key, _ = load_verify_notice_access_keys()
    verify_resp = post_verify_check(
        verify_access_key=verify_access_key,
        code_id=event.verify_code_id,
        code=code,
    )
    if not verify_resp or verify_resp.get("errorCode") != 0:
        update_event_status(
            event.id,
            status=EventStatusEnum.PENDING_VERIFY.value,
            message="waiting for verified",
        )
        raise ValueError("invalid or expired verify code")
    data = json.loads(event.payload_json or "{}")
    return event, data
