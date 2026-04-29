"""begin_transaction input validation (no database)."""

from django.test import SimpleTestCase

from app_tcc.services import coordinator


class BeginTransactionValidationTests(SimpleTestCase):
    def test_empty_branch_items(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(biz_id=1, branch_items=[], x_request_id=1)
        self.assertIn("branch_items", str(ctx.exception).lower())

    def test_biz_id_must_be_int(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id="1",  # type: ignore[arg-type]
                branch_items=[{"branch_code": "a"}],
                x_request_id=1,
            )
        self.assertIn("biz_id", str(ctx.exception).lower())

    def test_code_must_be_string(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[{"branch_code": 0}],  # type: ignore[dict-item]
                x_request_id=1,
            )
        self.assertIn("string", str(ctx.exception).lower())

    def test_duplicate_code_in_request(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[
                    {"branch_code": "a"},
                    {"branch_code": "a"},
                ],
                x_request_id=1,
            )
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_payload_must_be_object_when_provided(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.begin_transaction(
                biz_id=1,
                branch_items=[{"branch_code": "a", "payload": [1, 2]}],
                x_request_id=1,
            )
        self.assertIn("payload", str(ctx.exception).lower())
