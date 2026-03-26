import hashlib
import hmac
import time
import uuid


def build_signature(secret: str, timestamp_sec: str, raw_body: bytes) -> str:
    canonical = timestamp_sec.encode("utf-8") + b"." + raw_body
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def callback_headers(secret: str, raw_body: bytes) -> dict:
    ts = str(int(time.time()))
    sig = build_signature(secret, ts, raw_body)
    return {
        "Content-Type": "application/json",
        "X-AIBroker-Timestamp": ts,
        "X-AIBroker-Signature": sig,
        "X-AIBroker-Delivery-Id": str(uuid.uuid4()),
    }
