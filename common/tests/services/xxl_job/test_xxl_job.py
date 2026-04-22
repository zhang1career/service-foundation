from __future__ import annotations

import os
from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings

from common.services.xxl_job import (
    get_registry,
    parse_run_body,
    read_access_token,
    reset_registry_for_tests,
    run_sync,
    validate_token,
)


class TokenTests(TestCase):
    def test_validate_token(self) -> None:
        self.assertFalse(validate_token(provided=None, expected="a"))
        self.assertTrue(validate_token(provided="a", expected="a"))

    def test_read_access_token(self) -> None:
        rf = RequestFactory()
        r = rf.get("/")
        r.META["HTTP_XXL_JOB_ACCESS_TOKEN"] = "from-meta"
        self.assertEqual(read_access_token(r), "from-meta")


class ParseRunBodyTests(TestCase):
    def test_ok(self) -> None:
        p = parse_run_body(
            {
                "jobId": 1,
                "logId": 2,
                "executorHandler": "sagaScan",
                "executorParams": " 50 ",
            }
        )
        self.assertEqual(p.executor_handler, "sagaScan")
        self.assertEqual(p.executor_params, " 50 ")

    def test_params_optional(self) -> None:
        p = parse_run_body(
            {
                "jobId": 10,
                "logId": 20,
                "executorHandler": "h",
            }
        )
        self.assertIsNone(p.executor_params)


class RunnerRegistryTests(TestCase):
    def tearDown(self) -> None:
        reset_registry_for_tests()

    @override_settings(
        XXL_JOB_TOKEN="k",
        XXL_JOB_ADMIN_ADDRESS="http://{{xxl-adm}}/xxl-job-admin",
    )
    @patch.dict(os.environ, {"SERVICE_HOST_XXL_ADM": "admin.internal:9999"}, clear=False)
    @patch("common.services.xxl_job.callback.request_sync")
    def test_resolved_admin_url(self, m_req) -> None:
        m_req.return_value.status_code = 200
        r = get_registry()
        r.register("h1", lambda p: (True, "x"))
        run_sync(
            registry=r, executor_handler="h1", executor_params=None, log_id=1
        )
        self.assertIn("admin.internal:9999/xxl-job-admin/api/callback", m_req.call_args[1]["url"])

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_happy(self, m_req) -> None:
        m_req.return_value.status_code = 200
        r = get_registry()
        r.register("h1", lambda p: (True, "done"))
        run_sync(registry=r, executor_handler="h1", executor_params="x", log_id=99)
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["logId"], 99)
        self.assertEqual(b["handleCode"], 200)
        self.assertEqual(b["handleMsg"], "done")

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="")
    def test_skip_callback_no_admin(self) -> None:
        with patch("common.services.xxl_job.callback.request_sync") as m_req:
            r = get_registry()
            r.register("h1", lambda p: (True, "ok"))
            run_sync(registry=r, executor_handler="h1", executor_params=None, log_id=1)
            m_req.assert_not_called()

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_unknown_handler(self, m_req) -> None:
        m_req.return_value.status_code = 200
        run_sync(
            registry=get_registry(), executor_handler="nope", executor_params=None, log_id=3
        )
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["handleCode"], 500)
        self.assertIn("unknown handler", b["handleMsg"])
