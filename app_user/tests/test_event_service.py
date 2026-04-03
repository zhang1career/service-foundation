from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_user.services.event_service import EventService, _to_dict
from common.consts.query_const import LIMIT_LIST, LIMIT_PAGE


def _event(**kwargs):
    base = dict(
        id=1,
        biz_type=1,
        status=1,
        level=1,
        verify_code_id=0,
        verify_ref_id=0,
        notice_target="",
        notice_channel=0,
        payload_json="{}",
        message="",
        ct=1,
        ut=2,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestEventServiceToDict(SimpleTestCase):
    def test_to_dict_maps_fields(self):
        e = _event(id=9, message="m")
        d = _to_dict(e)
        self.assertEqual(d["id"], 9)
        self.assertEqual(d["message"], "m")


class TestEventServiceList(SimpleTestCase):
    @patch("app_user.services.event_service.list_events")
    def test_list_clamps_high_limit(self, mock_list):
        mock_list.return_value = ([], 0)
        EventService.list_events(offset=0, limit=10_000)
        mock_list.assert_called_once_with(offset=0, limit=LIMIT_LIST)

    @patch("app_user.services.event_service.list_events")
    def test_list_non_positive_limit_uses_page_default(self, mock_list):
        mock_list.return_value = ([], 0)
        EventService.list_events(offset=0, limit=-1)
        mock_list.assert_called_once_with(offset=0, limit=LIMIT_PAGE)

    @patch("app_user.services.event_service.list_events")
    def test_list_returns_page_shape(self, mock_list):
        row = _event(id=1)
        mock_list.return_value = ([row], 1)
        page = EventService.list_events(offset=0, limit=10)
        self.assertEqual(page["total_num"], 1)
        self.assertEqual(len(page["data"]), 1)
        self.assertEqual(page["data"][0]["id"], 1)


class TestEventServiceGetUpdateDelete(SimpleTestCase):
    @patch("app_user.services.event_service.get_event_by_id")
    def test_get_event_none(self, mock_get):
        mock_get.return_value = None
        self.assertIsNone(EventService.get_event(1))

    @patch("app_user.services.event_service.get_event_by_id")
    def test_get_event_found(self, mock_get):
        mock_get.return_value = _event(id=3)
        d = EventService.get_event(3)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d["id"], 3)

    @patch("app_user.services.event_service.update_event_fields")
    def test_update_event_by_payload_empty_payload_no_repo_keys(self, mock_upd):
        mock_upd.return_value = None
        self.assertIsNone(EventService.update_event_by_payload(1, {}))

    @patch("app_user.services.event_service.update_event_fields")
    def test_update_event_by_payload_passes_int_fields(self, mock_upd):
        row = _event(id=1, status=2)
        mock_upd.return_value = row
        payload = {
            "biz_type": 1,
            "status": 2,
            "level": 3,
            "verify_code_id": 4,
            "verify_ref_id": 5,
            "notice_channel": 6,
        }
        out = EventService.update_event_by_payload(1, payload)
        mock_upd.assert_called_once()
        call_kw = mock_upd.call_args.kwargs
        self.assertEqual(call_kw["biz_type"], 1)
        self.assertEqual(call_kw["status"], 2)
        self.assertEqual(out["status"], 2)

    @patch("app_user.services.event_service.update_event_fields")
    def test_update_strips_notice_target_and_message(self, mock_upd):
        mock_upd.return_value = _event()
        EventService.update_event_by_payload(
            1,
            {"notice_target": "  a@b.c  ", "message": "  hi  "},
        )
        kw = mock_upd.call_args.kwargs
        self.assertEqual(kw["notice_target"], "a@b.c")
        self.assertEqual(kw["message"], "hi")

    @patch("app_user.services.event_service.delete_event")
    def test_delete_event(self, mock_del):
        mock_del.return_value = True
        self.assertTrue(EventService.delete_event(7))
        mock_del.assert_called_once_with(event_id=7)
