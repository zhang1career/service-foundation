"""outbound_http — TCC branch_id → branch_code rewrite (no HTTP)."""

from django.test import SimpleTestCase

from app_saga.services import outbound_http


class TccBranchRewriteTests(SimpleTestCase):
    def test_prepare_rewrites_branches_in_payload(self):
        body = {
            "payload": {
                "biz_id": 1,
                "branches": [
                    {"branch_id": "pay", "payload": {"x": 1}},
                ],
            }
        }
        out = outbound_http.prepare_saga_outbound_json_body(body)
        self.assertNotIn("branch_id", out["payload"]["branches"][0])
        self.assertEqual(out["payload"]["branches"][0]["branch_code"], "pay")
        # original structure unchanged
        self.assertIn("branch_id", body["payload"]["branches"][0])

    def test_branch_code_preserved_drops_branch_id(self):
        body = {
            "payload": {
                "branches": [{"branch_id": "old", "branch_code": "keep"}],
            }
        }
        out = outbound_http.prepare_saga_outbound_json_body(body)
        el = out["payload"]["branches"][0]
        self.assertEqual(el["branch_code"], "keep")
        self.assertNotIn("branch_id", el)

    def test_non_string_branch_id_stringified(self):
        body = {"payload": {"branches": [{"branch_id": 7}]}}
        out = outbound_http.prepare_saga_outbound_json_body(body)
        self.assertEqual(out["payload"]["branches"][0]["branch_code"], "7")
