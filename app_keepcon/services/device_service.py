from __future__ import annotations

from app_keepcon.enums.device_type_enum import KeepconDeviceType
from app_keepcon.repos import device_repo, message_repo


def _device_to_dict(dev) -> dict:
    try:
        dt_label = KeepconDeviceType(dev.device_type).name.lower()
    except ValueError:
        dt_label = str(dev.device_type)
    return {
        "id": dev.id,
        "device_key": dev.device_key,
        "secret": dev.secret,
        "device_type": dev.device_type,
        "device_type_label": dt_label,
        "name": dev.name,
        "status": dev.status,
        "next_seq": dev.next_seq,
        "last_seen_at": dev.last_seen_at,
        "ct": dev.ct,
        "ut": dev.ut,
    }


def _message_to_dict(msg) -> dict:
    return {
        "id": msg.id,
        "device_id": msg.device_id,
        "seq": msg.seq,
        "payload": msg.payload,
        "status": msg.status,
        "idem_key": msg.idem_key,
        "ct": msg.ct,
    }


class KeepconDeviceService:
    @staticmethod
    def list_all() -> list:
        return [_device_to_dict(d) for d in device_repo.list_devices()]

    @staticmethod
    def create(device_key: str, device_type: int | str = KeepconDeviceType.MOBILE, name: str = "") -> dict:
        dev = device_repo.create_device(
            device_key=device_key,
            device_type=device_type,
            name=name,
            status=1,
        )
        return _device_to_dict(dev)

    @staticmethod
    def update(device_row_id: int, payload: dict) -> dict:
        name = payload.get("name") if "name" in payload else None
        device_type = payload.get("device_type") if "device_type" in payload else None
        status = int(payload["status"]) if "status" in payload else None
        dev = device_repo.update_device(device_row_id, name=name, device_type=device_type, status=status)
        if not dev:
            raise ValueError("device not found")
        return _device_to_dict(dev)

    @staticmethod
    def delete(device_row_id: int) -> bool:
        if not device_repo.delete_device(device_row_id):
            raise ValueError("device not found")
        return True

    @staticmethod
    def sync_payloads_since(device_row_id: int, since_seq: int) -> list[dict]:
        rows = message_repo.list_pending_since_seq(device_row_id, since_seq, limit=50)
        return [_message_to_dict(m) for m in rows]

    @staticmethod
    def ack(device_row_id: int, msg_id: int) -> dict:
        msg = message_repo.mark_acked(msg_id, device_row_id)
        if not msg:
            raise ValueError("message not found")
        return _message_to_dict(msg)


class KeepconMessageService:
    @staticmethod
    def list_for_console(device_row_id: int | None = None, limit: int = 200) -> list[dict]:
        if device_row_id is not None:
            return [
                {**_message_to_dict(m), "device_key": m.device.device_key}
                for m in message_repo.list_messages_for_device(device_row_id, limit=limit)
            ]
        return [
            {**_message_to_dict(m), "device_key": m.device.device_key}
            for m in message_repo.list_recent_messages(limit=limit)
        ]
