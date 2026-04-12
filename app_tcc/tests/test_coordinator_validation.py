"""begin_transaction input validation (no database)."""

from django.test import SimpleTestCase

from app_tcc.services import coordinator


class BeginTransactionValidationTests(SimpleTestCase):
    def test_empty_branch_items(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(branch_items=[])
        self.assertIn("branch_items", str(ctx.exception).lower())

    def test_branch_meta_id_must_be_int(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(branch_items=[{"branch_meta_id": "1"}])
        self.assertIn("int", str(ctx.exception))

    def test_duplicate_branch_meta_id_in_request(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                branch_items=[
                    {"branch_meta_id": 1},
                    {"branch_meta_id": 1},
                ],
            )
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_payload_must_be_object_when_provided(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                branch_items=[{"branch_meta_id": 1, "payload": [1, 2]}],
            )
        self.assertIn("payload", str(ctx.exception).lower())
