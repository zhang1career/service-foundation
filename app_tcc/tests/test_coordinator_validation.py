"""begin_transaction input validation (no database)."""

from django.test import SimpleTestCase

from app_tcc.services import coordinator


class BeginTransactionValidationTests(SimpleTestCase):
    def test_empty_branch_items(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(biz_id=1, branch_items=[])
        self.assertIn("branch_items", str(ctx.exception).lower())

    def test_biz_id_must_be_int(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id="1",  # type: ignore[arg-type]
                branch_items=[{"branch_index": 0}],
            )
        self.assertIn("biz_id", str(ctx.exception).lower())

    def test_branch_index_must_be_int(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[{"branch_index": "0"}],
            )
        self.assertIn("int", str(ctx.exception))

    def test_duplicate_branch_index_in_request(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[
                    {"branch_index": 0},
                    {"branch_index": 0},
                ],
            )
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_payload_must_be_object_when_provided(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[{"branch_index": 0, "payload": [1, 2]}],
            )
        self.assertIn("payload", str(ctx.exception).lower())
