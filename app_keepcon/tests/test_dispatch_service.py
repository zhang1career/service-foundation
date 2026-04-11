"""Tests for dispatch_to_device (mocked DB + channel layer)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_keepcon.models import KeepconMessage
from app_keepcon.services.dispatch_service import dispatch_to_device, ws_group_name


class TestWsGroupName(SimpleTestCase):
    def test_prefix(self):
        self.assertEqual(ws_group_name("d1"), "keepcon_d1")


class TestDispatchToDevice(SimpleTestCase):
    @patch("app_keepcon.services.dispatch_service.async_to_sync")
    @patch("app_keepcon.services.dispatch_service.get_channel_layer")
    @patch("app_keepcon.services.dispatch_service.device_repo.allocate_seq_and_create_message")
    @patch("app_keepcon.services.dispatch_service.device_repo.get_device_by_key")
    def test_dispatch_dict_payload_calls_group_send(
        self,
        mock_get_dev,
        mock_alloc,
        mock_get_layer,
        mock_a2s,
    ):
        dev = SimpleNamespace(id=7, device_key="my-device", status=1)
        mock_get_dev.return_value = dev
        msg = SimpleNamespace(id=100, seq=3, status=KeepconMessage.MSG_PENDING)
        mock_alloc.return_value = (dev, msg)
        layer = MagicMock()
        mock_get_layer.return_value = layer
        sync_send = MagicMock()
        mock_a2s.return_value = sync_send

        out = dispatch_to_device("my-device", {"hello": "world"}, idem_key=None)

        mock_get_dev.assert_called_once_with("my-device")
        mock_alloc.assert_called_once()
        mock_a2s.assert_called_once()
        sync_send.assert_called_once()
        call_args = sync_send.call_args[0]
        self.assertEqual(call_args[0], "keepcon_my-device")
        self.assertEqual(call_args[1]["type"], "push.message")
        self.assertEqual(call_args[1]["envelope"]["msg_id"], 100)
        self.assertEqual(call_args[1]["envelope"]["seq"], 3)
        self.assertEqual(out["msg_id"], 100)
        self.assertEqual(out["seq"], 3)

    @patch("app_keepcon.services.dispatch_service.device_repo.get_device_by_key")
    def test_dispatch_missing_device_raises(self, mock_get_dev):
        mock_get_dev.return_value = None
        with self.assertRaises(ValueError) as ctx:
            dispatch_to_device("x", {})
        self.assertIn("device not found", str(ctx.exception))

    @patch("app_keepcon.services.dispatch_service.device_repo.get_device_by_key")
    def test_dispatch_disabled_device_raises(self, mock_get_dev):
        mock_get_dev.return_value = SimpleNamespace(id=1, device_key="x", status=0)
        with self.assertRaises(ValueError):
            dispatch_to_device("x", {})

    @patch("app_keepcon.services.dispatch_service.async_to_sync")
    @patch("app_keepcon.services.dispatch_service.get_channel_layer")
    @patch("app_keepcon.services.dispatch_service.device_repo.allocate_seq_and_create_message")
    @patch("app_keepcon.services.dispatch_service.device_repo.get_device_by_key")
    def test_dispatch_list_payload_envelope_is_list(
        self,
        mock_get_dev,
        mock_alloc,
        mock_get_layer,
        mock_a2s,
    ):
        dev = SimpleNamespace(id=1, device_key="d", status=1)
        mock_get_dev.return_value = dev
        msg = SimpleNamespace(id=5, seq=1, status=KeepconMessage.MSG_PENDING)
        mock_alloc.return_value = (dev, msg)
        mock_get_layer.return_value = MagicMock()
        sync_send = MagicMock()
        mock_a2s.return_value = sync_send

        dispatch_to_device("d", [1, "b", 3], idem_key=None)

        env = sync_send.call_args[0][1]["envelope"]
        self.assertEqual(env["payload"], [1, "b", 3])

    @patch("app_keepcon.services.dispatch_service.async_to_sync")
    @patch("app_keepcon.services.dispatch_service.get_channel_layer")
    @patch("app_keepcon.services.dispatch_service.device_repo.allocate_seq_and_create_message")
    @patch("app_keepcon.services.dispatch_service.device_repo.get_device_by_key")
    def test_dispatch_scalar_payload_wraps_in_value_json(
        self,
        mock_get_dev,
        mock_alloc,
        mock_get_layer,
        mock_a2s,
    ):
        dev = SimpleNamespace(id=2, device_key="dev2", status=1)
        mock_get_dev.return_value = dev
        msg = SimpleNamespace(id=6, seq=2, status=KeepconMessage.MSG_PENDING)
        mock_alloc.return_value = (dev, msg)
        mock_get_layer.return_value = MagicMock()
        sync_send = MagicMock()
        mock_a2s.return_value = sync_send

        dispatch_to_device("dev2", 42, idem_key="ik")

        mock_alloc.assert_called_once()
        _dev_id, payload_json, idem = mock_alloc.call_args[0]
        self.assertEqual(idem, "ik")
        self.assertIn("42", payload_json)
        env = sync_send.call_args[0][1]["envelope"]
        self.assertEqual(env["payload"], 42)
