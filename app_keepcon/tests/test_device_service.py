"""Tests for KeepconDeviceService / KeepconMessageService (mocked repos)."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_keepcon.enums.device_type_enum import KeepconDeviceType
from app_keepcon.services.device_service import KeepconDeviceService, KeepconMessageService


class TestKeepconDeviceService(SimpleTestCase):
    @patch("app_keepcon.services.device_service.device_repo.list_devices")
    def test_list_all_maps_device_type_label(self, mock_list):
        mock_list.return_value = [
            SimpleNamespace(
                id=1,
                device_key="k1",
                secret="s",
                device_type=int(KeepconDeviceType.WEB),
                name="",
                status=1,
                next_seq=0,
                last_seen_at=0,
                ct=0,
                ut=0,
            ),
        ]
        rows = KeepconDeviceService.list_all()
        self.assertEqual(rows[0]["device_type"], 2)
        self.assertEqual(rows[0]["device_type_label"], "web")

    @patch("app_keepcon.services.device_service.device_repo.create_device")
    def test_create_delegates_to_repo(self, mock_create):
        mock_create.return_value = SimpleNamespace(
            id=5,
            device_key="dk",
            secret="sec",
            device_type=1,
            name="n",
            status=1,
            next_seq=0,
            last_seen_at=0,
            ct=1,
            ut=2,
        )
        out = KeepconDeviceService.create("dk", device_type="mobile", name="n")
        mock_create.assert_called_once()
        self.assertEqual(out["device_key"], "dk")
        self.assertEqual(out["device_type_label"], "mobile")

    @patch("app_keepcon.services.device_service.device_repo.list_devices")
    def test_list_all_unknown_device_type_uses_string_label(self, mock_list):
        mock_list.return_value = [
            SimpleNamespace(
                id=2,
                device_key="k",
                secret="s",
                device_type=99,
                name="",
                status=1,
                next_seq=0,
                last_seen_at=0,
                ct=0,
                ut=0,
            ),
        ]
        rows = KeepconDeviceService.list_all()
        self.assertEqual(rows[0]["device_type_label"], "99")

    @patch("app_keepcon.services.device_service.device_repo.update_device")
    def test_update_success(self, mock_update):
        mock_update.return_value = SimpleNamespace(
            id=3,
            device_key="dk",
            secret="s",
            device_type=2,
            name="nn",
            status=1,
            next_seq=1,
            last_seen_at=0,
            ct=0,
            ut=0,
        )
        out = KeepconDeviceService.update(
            3,
            {"name": "nn", "device_type": 2, "status": 1},
        )
        mock_update.assert_called_once()
        self.assertEqual(out["name"], "nn")
        self.assertEqual(out["device_type"], 2)

    @patch("app_keepcon.services.device_service.device_repo.update_device")
    def test_update_not_found_raises(self, mock_update):
        mock_update.return_value = None
        with self.assertRaises(ValueError) as ctx:
            KeepconDeviceService.update(99, {"name": "x"})
        self.assertEqual(str(ctx.exception), "device not found")

    @patch("app_keepcon.services.device_service.device_repo.delete_device")
    def test_delete_success(self, mock_delete):
        mock_delete.return_value = True
        self.assertTrue(KeepconDeviceService.delete(4))
        mock_delete.assert_called_once_with(4)

    @patch("app_keepcon.services.device_service.device_repo.delete_device")
    def test_delete_not_found_raises(self, mock_delete):
        mock_delete.return_value = False
        with self.assertRaises(ValueError) as ctx:
            KeepconDeviceService.delete(5)
        self.assertEqual(str(ctx.exception), "device not found")

    @patch("app_keepcon.services.device_service.message_repo.list_pending_since_seq")
    def test_sync_payloads_since(self, mock_list):
        mock_list.return_value = [
            SimpleNamespace(
                id=1,
                device_id=1,
                seq=2,
                payload='{"a":1}',
                status=0,
                idem_key=None,
                ct=1,
            ),
        ]
        rows = KeepconDeviceService.sync_payloads_since(1, since_seq=1)
        mock_list.assert_called_once_with(1, 1, limit=50)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["seq"], 2)

    @patch("app_keepcon.services.device_service.message_repo.mark_acked")
    def test_ack_success(self, mock_ack):
        mock_ack.return_value = SimpleNamespace(
            id=10,
            device_id=1,
            seq=3,
            payload="{}",
            status=2,
            idem_key=None,
            ct=1,
        )
        out = KeepconDeviceService.ack(1, 10)
        mock_ack.assert_called_once_with(10, 1)
        self.assertEqual(out["status"], 2)

    @patch("app_keepcon.services.device_service.message_repo.mark_acked")
    def test_ack_not_found_raises(self, mock_ack):
        mock_ack.return_value = None
        with self.assertRaises(ValueError) as ctx:
            KeepconDeviceService.ack(1, 999)
        self.assertEqual(str(ctx.exception), "message not found")


class TestKeepconMessageService(SimpleTestCase):
    @patch("app_keepcon.services.device_service.message_repo.list_recent_messages")
    def test_list_for_console_all_devices(self, mock_list):
        dev = SimpleNamespace(device_key="dev-a")
        msg = SimpleNamespace(
            id=10,
            device_id=1,
            seq=1,
            payload="{}",
            status=0,
            idem_key=None,
            ct=100,
            device=dev,
        )
        mock_list.return_value = [msg]
        rows = KeepconMessageService.list_for_console()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["device_key"], "dev-a")
        self.assertEqual(rows[0]["seq"], 1)

    @patch("app_keepcon.services.device_service.message_repo.list_messages_for_device")
    def test_list_for_console_single_device_filter(self, mock_list):
        dev = SimpleNamespace(device_key="filtered")
        msg = SimpleNamespace(
            id=20,
            device_id=5,
            seq=1,
            payload="{}",
            status=0,
            idem_key="k",
            ct=2,
            device=dev,
        )
        mock_list.return_value = [msg]
        rows = KeepconMessageService.list_for_console(device_row_id=5, limit=50)
        mock_list.assert_called_once_with(5, limit=50)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["device_key"], "filtered")
        self.assertEqual(rows[0]["idem_key"], "k")
