from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase, override_settings

from common.services.service_discovery import reset_service_discovery_redis_client_for_tests
from common.services.xxl_job import (
    get_registry,
    parse_run_body,
    read_access_token,
    reset_registry_for_tests,
    run_sync,
    validate_token,
)
from common.services.xxl_job.callback import send_callback


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
                "logDateTime": 1700000000001,
                "executorHandler": "sagaScan",
                "executorParams": " 50 ",
            }
        )
        self.assertEqual(p.executor_handler, "sagaScan")
        self.assertEqual(p.executor_params, " 50 ")
        self.assertEqual(p.log_date_time_ms, 1700000000001)

    def test_params_optional(self) -> None:
        p = parse_run_body(
            {
                "jobId": 10,
                "logId": 20,
                "logDateTime": 1700000000002,
                "executorHandler": "h",
            }
        )
        self.assertIsNone(p.executor_params)
        self.assertEqual(p.log_date_time_ms, 1700000000002)


class RunnerRegistryTests(TestCase):
    def tearDown(self) -> None:
        reset_registry_for_tests()
        reset_service_discovery_redis_client_for_tests()

    @override_settings(
        XXL_JOB_TOKEN="k",
        XXL_JOB_ADMIN_ADDRESS="http://{{xxl-adm}}/xxl-job-admin",
        SERVICE_DISCOVERY_KEY_PREFIX="",
    )
    @patch("common.services.service_discovery.expand._get_redis_client")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_resolved_admin_url(self, m_req, m_grc) -> None:
        m_client = MagicMock()
        m_client.get.return_value = "admin.internal:9999"
        m_grc.return_value = m_client
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":200}'
        r = get_registry()
        r.register("h1", lambda p: (True, "x"))
        out = run_sync(
            registry=r,
            executor_handler="h1",
            executor_params=None,
            log_id=1,
            log_date_time_ms=1700000000003,
        )
        self.assertEqual(out, (True, "x"))
        self.assertIn("admin.internal:9999/xxl-job-admin/api/callback", m_req.call_args[1]["url"])

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_happy(self, m_req) -> None:
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":200}'
        r = get_registry()
        r.register("h1", lambda p: (True, "done"))
        self.assertEqual(
            run_sync(
                registry=r,
                executor_handler="h1",
                executor_params="x",
                log_id=99,
                log_date_time_ms=1700000000099,
            ),
            (True, "done"),
        )
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["logId"], 99)
        self.assertEqual(b["handleCode"], 200)
        self.assertEqual(b["handleMsg"], "done")
        self.assertEqual(b["logDateTim"], 1700000000099)

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_send_callback_false_when_admin_return_t_not_success(self, m_req) -> None:
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":500,"msg":"bad token"}'
        self.assertFalse(
            send_callback(
                log_id=7,
                log_date_tim=1700000000007,
                handle_code=200,
                handle_msg="handler ok",
            ),
        )

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_success_handler_empty_message_sends_ok(self, m_req) -> None:
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":200}'
        r = get_registry()
        r.register("h_empty", lambda p: (True, "   "))
        self.assertEqual(
            run_sync(
                registry=r,
                executor_handler="h_empty",
                executor_params=None,
                log_id=5,
                log_date_time_ms=1700000000005,
            ),
            (True, "   "),
        )
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["handleMsg"], "OK")

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="")
    def test_skip_callback_no_admin(self) -> None:
        with patch("common.services.xxl_job.callback.request_sync") as m_req:
            r = get_registry()
            r.register("h1", lambda p: (True, "ok"))
            self.assertEqual(
                run_sync(
                    registry=r,
                    executor_handler="h1",
                    executor_params=None,
                    log_id=1,
                    log_date_time_ms=1700000000001,
                ),
                (True, "ok"),
            )
            m_req.assert_not_called()

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_unknown_handler(self, m_req) -> None:
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":200}'
        out = run_sync(
            registry=get_registry(),
            executor_handler="nope",
            executor_params=None,
            log_id=3,
            log_date_time_ms=1700000000003,
        )
        self.assertFalse(out[0])
        self.assertIn("unknown handler", out[1])
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["handleCode"], 500)
        self.assertIn("unknown handler", b["handleMsg"])

    @override_settings(XXL_JOB_TOKEN="k", XXL_JOB_ADMIN_ADDRESS="http://a/x")
    @patch("common.services.xxl_job.callback.request_sync")
    def test_dict_payload_callback_json_encode_like_paganini(self, m_req) -> None:
        m_req.return_value.status_code = 200
        m_req.return_value.text = '{"code":200}'
        r = get_registry()
        r.register("h_dict", lambda p: (True, {"closed": 0, "errors": 0}))
        self.assertEqual(
            run_sync(
                registry=r,
                executor_handler="h_dict",
                executor_params=None,
                log_id=8,
                log_date_time_ms=1700000000008,
            ),
            (True, {"closed": 0, "errors": 0}),
        )
        b = m_req.call_args[1]["json_body"][0]
        self.assertEqual(b["handleCode"], 200)
        self.assertEqual(b["handleMsg"], '{"closed":0,"errors":0}')
