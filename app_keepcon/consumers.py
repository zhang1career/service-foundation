"""WebSocket consumer: hello / sync / ack; receives push via group_send."""

import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from app_keepcon.repos import device_repo, message_repo
from app_keepcon.services.device_service import KeepconDeviceService
from app_keepcon.services.dispatch_service import ws_group_name


class KeepconConsumer(AsyncWebsocketConsumer):
    device_row_id: int | None
    device_key: str | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_row_id = None
        self.device_key = None

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if self.device_key:
            await self.channel_layer.group_discard(
                ws_group_name(self.device_key),
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps({"type": "error", "message": "invalid json"}),
            )
            return

        msg_type = (data.get("type") or "").strip()
        if msg_type == "hello":
            await self._handle_hello(data)
        elif msg_type == "sync":
            await self._handle_sync(data)
        elif msg_type == "ack":
            await self._handle_ack(data)
        elif msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
        else:
            await self.send(
                text_data=json.dumps({"type": "error", "message": "unknown type"}),
            )

    async def _handle_hello(self, data: dict):
        device_key = (data.get("device_key") or "").strip()
        secret = (data.get("secret") or "").strip()
        dev = await sync_to_async(device_repo.authenticate_device)(device_key, secret)
        if not dev:
            await self.send(
                text_data=json.dumps({"type": "hello_fail", "message": "auth failed"}),
            )
            await self.close()
            return
        self.device_row_id = dev.id
        self.device_key = dev.device_key
        await self.channel_layer.group_add(
            ws_group_name(self.device_key),
            self.channel_name,
        )
        await sync_to_async(device_repo.update_device_last_seen)(dev.id)
        await self.send(text_data=json.dumps({"type": "hello_ok", "device_key": dev.device_key}))

    async def _handle_sync(self, data: dict):
        if self.device_row_id is None:
            await self.send(text_data=json.dumps({"type": "error", "message": "send hello first"}))
            return
        try:
            since_seq = int(data.get("since_seq", 0))
        except (TypeError, ValueError):
            since_seq = 0
        rows = await sync_to_async(KeepconDeviceService.sync_payloads_since)(
            self.device_row_id,
            since_seq,
        )
        await self.send(text_data=json.dumps({"type": "sync_ok", "messages": rows}))

    async def _handle_ack(self, data: dict):
        if self.device_row_id is None:
            await self.send(text_data=json.dumps({"type": "error", "message": "send hello first"}))
            return
        try:
            msg_id = int(data.get("msg_id", 0))
        except (TypeError, ValueError):
            await self.send(text_data=json.dumps({"type": "error", "message": "invalid msg_id"}))
            return
        msg = await sync_to_async(message_repo.mark_acked)(msg_id, self.device_row_id)
        if not msg:
            await self.send(text_data=json.dumps({"type": "error", "message": "message not found"}))
            return
        await self.send(
            text_data=json.dumps({"type": "ack_ok", "msg_id": msg.id, "seq": msg.seq}),
        )

    async def push_message(self, event):
        envelope = event["envelope"]
        await self.send(text_data=json.dumps(envelope))
        if self.device_row_id is not None:
            await sync_to_async(message_repo.mark_delivered)(
                envelope["msg_id"],
                self.device_row_id,
            )
