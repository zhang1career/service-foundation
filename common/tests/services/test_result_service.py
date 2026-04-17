from unittest import TestCase
from unittest.mock import patch

from common.services import result_service as rs


class ResultServiceWhitelistTest(TestCase):
    @patch.dict(
        "common.consts.result_const.RESULT_INDEX_MAP",
        {
            1: {
                "module": "common.tests.fixtures.result_index_stub",
                "func": "stub_result_fn",
            },
        },
        clear=True,
    )
    def test_get_result_allows_whitelisted_pair(self):
        idx = {"m": "common.tests.fixtures.result_index_stub", "f": "stub_result_fn", "p": ""}
        result, err = rs.get_result(idx)
        self.assertIsNone(err)
        self.assertEqual(result, {"ok": True, "param_map": None})

    @patch.dict("common.consts.result_const.RESULT_INDEX_MAP", {}, clear=True)
    def test_get_result_rejects_unknown_pair(self):
        idx = {"m": "os", "f": "system", "p": ""}
        result, err = rs.get_result(idx)
        self.assertIsNone(result)
        self.assertEqual(err, "result index is not allowed")

    @patch.dict(
        "common.consts.result_const.RESULT_INDEX_MAP",
        {
            1: {
                "module": "common.tests.fixtures.result_index_stub",
                "func": "stub_result_fn",
            },
        },
        clear=True,
    )
    def test_get_result_generic_error_on_failure(self):
        idx = {
            "m": "common.tests.fixtures.result_index_stub",
            "f": "stub_result_fn",
            "p": "not-json",
        }
        result, err = rs.get_result(idx)
        self.assertIsNone(result)
        self.assertEqual(err, "execution failed")
