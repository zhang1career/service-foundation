"""participant_reg_service — mocks only, no DB.

See ``test_flow_admin_service_mocked`` for why decorated entrypoints are invoked
via ``.__wrapped__`` (Django ``Atomic`` decorator opens ``saga_rw`` before the
function body runs).
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_saga.models import SagaParticipant
from app_saga.services import participant_reg_service
from common.enums.service_reg_status_enum import ServiceRegStatus


class ParticipantRegServiceMockedTests(SimpleTestCase):
    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_list_participants_empty(self, mock_objects):
        mock_objects.using.return_value.all.return_value.order_by.return_value = []
        self.assertEqual(participant_reg_service.list_participants(), [])

    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_get_participant_by_id(self, mock_objects):
        p = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = p
        self.assertIs(participant_reg_service.get_participant_by_id(5), p)

    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_get_participant_by_access_key_found(self, mock_objects):
        p = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = p
        self.assertIs(participant_reg_service.get_participant_by_access_key("abc"), p)

    def test_get_participant_by_access_key_blank(self):
        self.assertIsNone(participant_reg_service.get_participant_by_access_key(""))
        self.assertIsNone(participant_reg_service.get_participant_by_access_key("  "))

    @patch("app_saga.services.participant_reg_service.uuid.uuid4")
    @patch.object(SagaParticipant, "save")
    def test_create_participant_strips_and_saves(self, mock_save, mock_uuid):
        mock_uuid.return_value.hex = "a" * 32
        p = participant_reg_service.create_participant.__wrapped__(name="  n  ")
        self.assertEqual(p.name, "n")
        self.assertEqual(p.access_key, "a" * 32)
        mock_save.assert_called_once_with(using="saga_rw")

    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_update_participant(self, mock_objects):
        p = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = p
        out = participant_reg_service.update_participant.__wrapped__(1, name="  z  ")
        self.assertIs(out, p)
        self.assertEqual(p.name, "z")
        p.save.assert_called_once_with(using="saga_rw")

    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_update_participant_missing_returns_none(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.first.return_value = None
        self.assertIsNone(participant_reg_service.update_participant.__wrapped__(999, name="x"))

    @patch("app_saga.services.participant_reg_service.SagaParticipant.objects")
    def test_delete_participant(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.delete.return_value = (1, {})
        self.assertTrue(participant_reg_service.delete_participant.__wrapped__(1))
        mock_objects.using.return_value.filter.return_value.delete.return_value = (0, {})
        self.assertFalse(participant_reg_service.delete_participant.__wrapped__(2))
