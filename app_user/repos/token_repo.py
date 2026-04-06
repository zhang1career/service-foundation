from django.db import transaction

from app_user.enums.token_status_enum import TokenStatusEnum
from app_user.models import Token
from common.utils.date_util import get_now_timestamp_ms


def deprecate_all_tokens_for_user(user_id: int) -> int:
    """Set status=deprecated for all in-use tokens for this user. Returns rows updated."""
    return (
        Token.objects.using("user_rw")
        .filter(user_id=user_id, status=TokenStatusEnum.IN_USE.value)
        .update(status=TokenStatusEnum.DEPRECATED.value)
    )


def access_token_in_use(*, user_id: int, access_token: str) -> bool:
    return (
        Token.objects.using("user_rw")
        .filter(
            user_id=user_id,
            token=access_token,
            status=TokenStatusEnum.IN_USE.value,
        )
        .exists()
    )


def refresh_token_in_use(*, user_id: int, refresh_token: str) -> bool:
    return (
        Token.objects.using("user_rw")
        .filter(
            user_id=user_id,
            refresh=refresh_token,
            status=TokenStatusEnum.IN_USE.value,
        )
        .exists()
    )


@transaction.atomic(using="user_rw")
def replace_session_tokens(
        *,
        user_id: int,
        access_token: str,
        refresh_token: str,
        access_expires_at_ms: int,
) -> None:
    """Deprecate existing in-use rows and insert the new session pair."""
    deprecate_all_tokens_for_user(user_id)
    now_ms = get_now_timestamp_ms()
    Token.objects.using("user_rw").create(
        user_id=user_id,
        token=access_token,
        refresh=refresh_token,
        status=TokenStatusEnum.IN_USE.value,
        expires_at=access_expires_at_ms,
        ct=now_ms,
    )


@transaction.atomic(using="user_rw")
def rotate_refresh_row(
        *,
        user_id: int,
        old_refresh_token: str,
        new_access_token: str,
        new_refresh_token: str,
        access_expires_at_ms: int,
) -> bool:
    """
    Deprecate the row matching old_refresh_token (in_use), then insert the new pair.
    Returns True if a row was rotated; False if no matching in_use refresh was found.
    """
    updated = (
        Token.objects.using("user_rw")
        .filter(
            user_id=user_id,
            refresh=old_refresh_token,
            status=TokenStatusEnum.IN_USE.value,
        )
        .update(status=TokenStatusEnum.DEPRECATED.value)
    )
    if updated == 0:
        return False
    now_ms = get_now_timestamp_ms()
    Token.objects.using("user_rw").create(
        user_id=user_id,
        token=new_access_token,
        refresh=new_refresh_token,
        status=TokenStatusEnum.IN_USE.value,
        expires_at=access_expires_at_ms,
        ct=now_ms,
    )
    return True
