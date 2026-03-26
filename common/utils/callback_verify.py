import hashlib
import hmac
import time
from typing import Tuple


def verify_callback(
    secret: str,
    raw_body: bytes,
    timestamp_header: str,
    signature_hex: str,
    max_skew_sec: int = 300,
) -> Tuple[bool, str]:
    """
    Verify an HTTP callback signed as HMAC-SHA256(secret, f"{ts}." + raw_body) with hex digest in header.
    Returns (ok, error_message).
    """
    try:
        ts = int(timestamp_header)
    except (TypeError, ValueError):
        return False, "invalid timestamp"
    now = int(time.time())
    if abs(now - ts) > max_skew_sec:
        return False, "timestamp out of window"
    expected = hmac.new(
        secret.encode("utf-8"),
        str(ts).encode("utf-8") + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_hex or ""):
        return False, "invalid signature"
    return True, ""
