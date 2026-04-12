"""Coordinator branch order: Try ascending, Confirm/Cancel descending.

Uses mocks only — no MySQL / tcc_rw.
"""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from app_tcc.enums import BranchStatus, GlobalTxStatus
from app_tcc.services import coordinator


class _FakeGlobalTx:
    def __init__(self):
        self.pk = 100
        self.idem_key = 0
        self.status = GlobalTxStatus.TRYING
        self.auto_confirm = True
        self.retry_count = 0
        self.phase_deadline_at = 0
        self.next_retry_at = 0
        self.await_confirm_deadline_at = None
        self.branches = MagicMock()
        self.manual_reason = ""

    def refresh_from_db(self):
        return None

    def save(self, *args, **kwargs):
        return None


@override_settings(
    TCC_SNOWFLAKE_ACCESS_KEY="k",
    TCC_PHASE_TRY_TIMEOUT_SECONDS=120,
    TCC_PHASE_CONFIRM_TIMEOUT_SECONDS=120,
    TCC_PHASE_CANCEL_TIMEOUT_SECONDS=120,
)
class CoordinatorOrderMockedTests(SimpleTestCase):
    def _wire_branch_orm(self, mock_branch_class, branch_by_pk: dict):
        def _get_branch(*args, **kw):
            pk = kw.get("pk")
            if pk is None and args:
                pk = args[0]
            return branch_by_pk[pk]

        mock_branch_class.objects.using.return_value.select_related.return_value.get.side_effect = (
            _get_branch
        )

    def _make_branch(self, *, pk: int, meta: MagicMock, g: _FakeGlobalTx, idem: int, payload: str):
        b = MagicMock()
        b.pk = pk
        b.branch_meta = meta
        b.branch_index = meta.branch_index
        b.payload = payload
        b.global_tx = g
        b.idem_key = idem
        b.status = BranchStatus.PENDING_TRY
        b.last_http_status = None
        b.last_error = ""
        b.branch_meta_id = meta.pk
        return b

    @patch("app_tcc.services.coordinator.TccManualReview.objects")
    @patch("app_tcc.services.coordinator.TccBranch")
    @patch("app_tcc.services.coordinator.TccGlobalTransaction")
    @patch("app_tcc.services.coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_tcc.services.coordinator.get_now_timestamp_ms", return_value=1_000_000)
    @patch("app_tcc.services.coordinator.load_branch_metas_for_begin")
    @patch("app_tcc.services.coordinator.allocate_snowflake_int")
    @patch("app_tcc.services.coordinator.participant_http.call_participant")
    def test_try_order_then_confirm_reverse(
        self,
        mock_call,
        mock_snowflake,
        mock_load,
        mock_now,
        mock_gtx_class,
        mock_branch_class,
        mock_mr_objects,
    ):
        self.assertEqual(mock_now(), 1_000_000)
        mock_snowflake.side_effect = [8000, 9001, 9002]
        mock_call.return_value = (200, "")

        meta_a = MagicMock()
        meta_a.pk = 10
        meta_a.branch_index = 0
        meta_a.try_url = "http://a/try"
        meta_a.confirm_url = "http://a/confirm"
        meta_a.cancel_url = "http://a/cancel"
        meta_b = MagicMock()
        meta_b.pk = 11
        meta_b.branch_index = 1
        meta_b.try_url = "http://b/try"
        meta_b.confirm_url = "http://b/confirm"
        meta_b.cancel_url = "http://b/cancel"
        mock_load.return_value = [meta_a, meta_b]

        g = _FakeGlobalTx()

        def create_g(**kwargs):
            g.idem_key = kwargs["idem_key"]
            g.status = kwargs["status"]
            g.phase_deadline_at = kwargs["phase_deadline_at"]
            g.next_retry_at = kwargs["next_retry_at"]
            g.auto_confirm = kwargs["auto_confirm"]
            return g

        mock_gtx_class.objects.create.side_effect = create_g

        branch_by_pk: dict[int, MagicMock] = {}

        def create_branch(**kwargs):
            meta = kwargs["branch_meta"]
            pk = 201 + int(meta.branch_index)
            b = self._make_branch(
                pk=pk,
                meta=meta,
                g=g,
                idem=kwargs["idem_key"],
                payload=kwargs["payload"],
            )
            branch_by_pk[pk] = b
            return b

        mock_branch_class.objects.create.side_effect = create_branch
        self._wire_branch_orm(mock_branch_class, branch_by_pk)

        g.branches.select_related.return_value.order_by.return_value = sorted(
            branch_by_pk.values(),
            key=lambda x: x.branch_index,
        )
        mock_mr_objects.using.return_value.filter.return_value.first.return_value = None

        coordinator.begin_transaction(
            branch_items=[
                {"branch_meta_id": 10, "payload": {"k": 1}},
                {"branch_meta_id": 11, "payload": {"k": 2}},
            ],
            auto_confirm=True,
        )

        try_calls = [c for c in mock_call.call_args_list if c[1]["phase"] == "try"]
        self.assertEqual(len(try_calls), 2)
        self.assertEqual(try_calls[0][1]["url"], "http://a/try")
        self.assertEqual(try_calls[1][1]["url"], "http://b/try")

        confirm_calls = [c for c in mock_call.call_args_list if c[1]["phase"] == "confirm"]
        self.assertEqual(confirm_calls[0][1]["url"], "http://b/confirm")
        self.assertEqual(confirm_calls[1][1]["url"], "http://a/confirm")

        self.assertEqual(g.idem_key, 8000)
        self.assertEqual(g.status, GlobalTxStatus.COMMITTED)
        self.assertEqual(branch_by_pk[201].status, BranchStatus.CONFIRM_SUCCEEDED)
        self.assertEqual(branch_by_pk[202].status, BranchStatus.CONFIRM_SUCCEEDED)

    @patch("app_tcc.services.coordinator.TccManualReview.objects")
    @patch("app_tcc.services.coordinator.TccBranch")
    @patch("app_tcc.services.coordinator.TccGlobalTransaction")
    @patch("app_tcc.services.coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_tcc.services.coordinator.get_now_timestamp_ms", return_value=1_000_000)
    @patch("app_tcc.services.coordinator.load_branch_metas_for_begin")
    @patch("app_tcc.services.coordinator.allocate_snowflake_int")
    @patch("app_tcc.services.coordinator.participant_http.call_participant")
    def test_try_failure_cancels_reverse_try_order(
        self,
        mock_call,
        mock_snowflake,
        mock_load,
        mock_now,
        mock_gtx_class,
        mock_branch_class,
        mock_mr_objects,
    ):
        self.assertEqual(mock_now(), 1_000_000)
        mock_snowflake.side_effect = [8000, 9001, 9002]

        def side_effect(**kwargs):
            if kwargs["url"] == "http://b/try":
                return (500, "fail")
            return (200, "")

        mock_call.side_effect = side_effect

        meta_a = MagicMock()
        meta_a.pk = 10
        meta_a.branch_index = 0
        meta_a.try_url = "http://a/try"
        meta_a.confirm_url = "http://a/confirm"
        meta_a.cancel_url = "http://a/cancel"
        meta_b = MagicMock()
        meta_b.pk = 11
        meta_b.branch_index = 1
        meta_b.try_url = "http://b/try"
        meta_b.confirm_url = "http://b/confirm"
        meta_b.cancel_url = "http://b/cancel"
        mock_load.return_value = [meta_a, meta_b]

        g = _FakeGlobalTx()

        def create_g(**kwargs):
            g.idem_key = kwargs["idem_key"]
            g.status = kwargs["status"]
            g.phase_deadline_at = kwargs["phase_deadline_at"]
            g.next_retry_at = kwargs["next_retry_at"]
            g.auto_confirm = kwargs["auto_confirm"]
            return g

        mock_gtx_class.objects.create.side_effect = create_g

        branch_by_pk: dict[int, MagicMock] = {}

        def create_branch(**kwargs):
            meta = kwargs["branch_meta"]
            pk = 201 + int(meta.branch_index)
            b = self._make_branch(
                pk=pk,
                meta=meta,
                g=g,
                idem=kwargs["idem_key"],
                payload=kwargs["payload"],
            )
            branch_by_pk[pk] = b
            return b

        mock_branch_class.objects.create.side_effect = create_branch
        self._wire_branch_orm(mock_branch_class, branch_by_pk)

        g.branches.select_related.return_value.order_by.return_value = sorted(
            branch_by_pk.values(),
            key=lambda x: x.branch_index,
        )
        mock_mr_objects.using.return_value.filter.return_value.first.return_value = None

        coordinator.begin_transaction(
            branch_items=[
                {"branch_meta_id": 10},
                {"branch_meta_id": 11},
            ],
            auto_confirm=True,
        )

        cancel_calls = [c for c in mock_call.call_args_list if c[1]["phase"] == "cancel"]
        self.assertEqual(len(cancel_calls), 1)
        self.assertEqual(cancel_calls[0][1]["url"], "http://a/cancel")

        self.assertEqual(g.status, GlobalTxStatus.ROLLED_BACK)
