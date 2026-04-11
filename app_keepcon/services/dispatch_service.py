"""Create outbound messages and fan-out to Channels group (WebSocket workers)."""
from __future__ import annotations

import json
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from app_keepcon.repos import device_repo


def ws_group_name(device_key: str) -> str:
    return f"keepcon_{device_key}"


def dispatch_to_device(
    device_key: str,
    payload: Any,
    idem_key: str | None = None,
) -> dict:
    """
    Persist message and notify WebSocket group. If no client connected, row stays pending.
    """
    dev = device_repo.get_device_by_key(device_key)
    if not dev or dev.status != 1:
        raise ValueError("device not found or disabled")
    if isinstance(payload, (dict, list)):
        payload_json = json.dumps(payload, ensure_ascii=False)
        payload_for_envelope: Any = payload
    else:
        payload_json = json.dumps({"value": payload}, ensure_ascii=False)
        payload_for_envelope = payload

    _dev, msg = device_repo.allocate_seq_and_create_message(
        dev.id,
        payload_json,
        idem_key,
    )

    envelope = {
        "type": "push",
        "msg_id": msg.id,
        "seq": msg.seq,
        "payload": payload_for_envelope,
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        ws_group_name(dev.device_key),
        {"type": "push.message", "envelope": envelope},
    )

    return {
        "msg_id": msg.id,
        "seq": msg.seq,
        "device_key": dev.device_key,
        "status": msg.status,
    }
