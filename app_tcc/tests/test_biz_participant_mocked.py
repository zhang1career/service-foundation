"""biz_branch_service and participant_reg_service — mocks only, no DB.

``@transaction.atomic(using="tcc_rw")`` opens a real DB alias when the public
entrypoint runs; patching ``transaction`` on the service module does not help
because the decorator closed over ``django.db.transaction.atomic`` at import
time. Tests call small helpers that contain the ORM/query logic (or model init)
without entering that atomic block.
"""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_tcc.services import biz_branch_service
from app_tcc.services import participant_reg_service
from common.enums.service_reg_status_enum import ServiceRegStatus


class BizBranchServiceMockedTests(SimpleTestCase):
    @patch("app_tcc.services.biz_branch_service.TccParticipant.objects")
    def test_create_biz_meta_requires_participant(self, mock_p):
        mock_p.using.return_value.filter.return_value.exists.return_value = False
        with self.assertRaises(ValueError) as ctx:
            biz_branch_service._ensure_participant_exists_for_biz(9_999_999_999)
        self.assertIn("participant", str(ctx.exception).lower())

    @patch("app_tcc.services.biz_branch_service.TccBranchMeta.objects")
    def test_load_branch_metas_unknown_id_raises(self, mock_bm):
        empty_qs = MagicMock()
        empty_qs.__iter__ = lambda self: iter([])
        mock_bm.using.return_value.filter.return_value.select_related.return_value = empty_qs
        with self.assertRaises(ValueError) as ctx:
            biz_branch_service.load_branch_metas_for_begin([1, 2])
        self.assertIn("unknown", str(ctx.exception).lower())

    @patch("django.db.transaction.atomic", lambda **kw: nullcontext())
    @patch("app_tcc.services.biz_branch_service.TccBranchMeta.objects")
    def test_reorder_branch_metas_raises_length_mismatch(self, mock_objects):
        m1 = MagicMock()
        m1.id = 1
        m1.branch_index = 0
        mock_objects.using.return_value.filter.return_value.order_by.return_value = [m1]
        with self.assertRaises(ValueError) as ctx:
            biz_branch_service.reorder_branch_metas_for_biz(1, [1, 2])
        self.assertIn("length", str(ctx.exception).lower())

    @patch("django.db.transaction.atomic", lambda **kw: nullcontext())
    @patch("app_tcc.services.biz_branch_service.TccBranchMeta.objects")
    def test_reorder_branch_metas_raises_id_set_mismatch(self, mock_objects):
        m1 = MagicMock()
        m1.id = 1
        m1.branch_index = 0
        mock_objects.using.return_value.filter.return_value.order_by.return_value = [m1]
        with self.assertRaises(ValueError) as ctx:
            biz_branch_service.reorder_branch_metas_for_biz(1, [2])
        self.assertIn("id set", str(ctx.exception).lower())


class ParticipantRegServiceMockedTests(SimpleTestCase):
    def test_build_participant_strips_fields(self):
        p = participant_reg_service._build_participant_for_insert(
            access_key=" k ",
            name=" n ",
            status=ServiceRegStatus.ENABLED.value,
        )
        self.assertEqual(p.access_key, "k")
        self.assertEqual(p.name, "n")
        self.assertEqual(p.status, ServiceRegStatus.ENABLED.value)
