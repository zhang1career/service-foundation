"""``User.auth_status`` bitmask."""

from app_verify.enums import ChannelEnum

AUTH_BIT_CONSOLE = 1 << 0
AUTH_BIT_EMAIL = 1 << 1
AUTH_BIT_PHONE = 1 << 2


def registration_bit_for_notice_channel(notice_channel: int) -> int:
    ch = int(notice_channel)
    if ch == ChannelEnum.EMAIL.value:
        return AUTH_BIT_EMAIL
    if ch == ChannelEnum.SMS.value:
        return AUTH_BIT_PHONE
    raise ValueError("unsupported notice_channel for registration auth bit")


def auth_status_detail_public(mask: int) -> dict[str, bool]:
    return {
        "console": bool(mask & AUTH_BIT_CONSOLE),
        "email": bool(mask & AUTH_BIT_EMAIL),
    }
