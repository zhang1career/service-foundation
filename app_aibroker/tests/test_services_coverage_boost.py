import json
import sys
import types
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import ANY, MagicMock, patch

from django.conf import settings

from app_aibroker.services.aibroker_oss_http_service import (
    _read_upload_body,
    put_object_http,
    put_uploaded_file,
)
from app_aibroker.services.asset_admin_service import AssetAdminService, _parse_content_type
from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.callback_service import deliver_callback
from app_aibroker.services.job_service import (
    JOB_DONE,
    JOB_FAILED,
    JOB_PENDING,
    JOB_RUNNING,
    _run_job,
    enqueue_job,
    job_to_dict,
)
from app_aibroker.services.metrics_service import summary_since
from app_aibroker.services.reg_service import RegService
from app_aibroker.services.template_admin_service import TemplateAdminService
from common.enums.content_type_enum import ContentTypeEnum
from common.services.http import HttpCallError

if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub


class _ChunkedFile:
    def __init__(self, chunks):
        self._chunks = chunks
        self.seek_calls = 0

    def seek(self, _pos):
        self.seek_calls += 1

    def chunks(self):
        return iter(self._chunks)


class ServicesCoverageBoostTest(TestCase):
    def test_read_upload_body_from_chunks(self):
        f = _ChunkedFile([b"a", b"b"])
        self.assertEqual(_read_upload_body(f), b"ab")
        self.assertEqual(f.seek_calls, 2)

    def test_read_upload_body_from_read_with_seek_error(self):
        class _F:
            def read(self):
                return b"xyz"

            def seek(self, _):
                raise OSError("no-seek")

        self.assertEqual(_read_upload_body(_F()), b"xyz")

    @patch("app_aibroker.services.aibroker_oss_http_service.request_sync")
    def test_put_object_http_success(self, request_sync_mock):
        request_sync_mock.return_value = SimpleNamespace(status_code=200, text="")
        with patch.object(settings, "AIBROKER_OSS_ENDPOINT", "https://oss.example.com", create=True):
            with patch.object(settings, "AIBROKER_OSS_BUCKET", "demo", create=True):
                url = put_object_http("x/a b.png", b"123", "image/png")
        self.assertEqual(url, "https://oss.example.com/demo/x/a%20b.png")

    def test_put_object_http_requires_settings(self):
        with patch.object(settings, "AIBROKER_OSS_ENDPOINT", "", create=True):
            with patch.object(settings, "AIBROKER_OSS_BUCKET", "", create=True):
                with self.assertRaisesRegex(RuntimeError, "must be configured"):
                    put_object_http("k", b"d", "text/plain")

    @patch("app_aibroker.services.aibroker_oss_http_service.request_sync")
    def test_put_object_http_non_200(self, request_sync_mock):
        request_sync_mock.return_value = SimpleNamespace(status_code=403, text="forbidden")
        with patch.object(settings, "AIBROKER_OSS_ENDPOINT", "https://oss.example.com", create=True):
            with patch.object(settings, "AIBROKER_OSS_BUCKET", "demo", create=True):
                with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
                    put_object_http("k", b"d", "text/plain")

    @patch("app_aibroker.services.aibroker_oss_http_service.request_sync")
    def test_put_object_http_httpcallerror(self, request_sync_mock):
        request_sync_mock.side_effect = HttpCallError("network")
        with patch.object(settings, "AIBROKER_OSS_ENDPOINT", "https://oss.example.com", create=True):
            with patch.object(settings, "AIBROKER_OSS_BUCKET", "demo", create=True):
                with self.assertRaisesRegex(RuntimeError, "oss put failed"):
                    put_object_http("k", b"d", "text/plain")

    @patch("app_aibroker.services.aibroker_oss_http_service.put_object_http")
    def test_put_uploaded_file(self, put_mock):
        put_mock.return_value = "https://oss/x"
        f = _ChunkedFile([b"12", b"34"])
        out = put_uploaded_file(f, "x.bin", "application/octet-stream")
        self.assertEqual(out, "https://oss/x")
        put_mock.assert_called_once_with("x.bin", b"1234", "application/octet-stream")

    def test_parse_content_type(self):
        self.assertEqual(_parse_content_type(None), ContentTypeEnum.APPLICATION_OCTET_STREAM.value)
        self.assertEqual(
            _parse_content_type(str(ContentTypeEnum.IMAGE_PNG.value)),
            ContentTypeEnum.IMAGE_PNG.value,
        )
        with self.assertRaisesRegex(ValueError, "invalid content_type"):
            _parse_content_type("999")

    @patch("app_aibroker.services.asset_admin_service.create_asset")
    def test_asset_admin_create_for_reg(self, create_asset_mock):
        create_asset_mock.return_value = SimpleNamespace(
            id=1,
            oss_bucket="b",
            oss_key="k",
            content_type=ContentTypeEnum.IMAGE_PNG.value,
            ct=123,
        )
        data = AssetAdminService.create_for_reg(10, {"oss_bucket": " b ", "oss_key": " k "})
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["oss_bucket"], "b")

    def test_asset_admin_create_for_reg_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "required"):
            AssetAdminService.create_for_reg(10, {"oss_bucket": "", "oss_key": ""})

    @patch("app_aibroker.services.asset_admin_service.get_asset_by_id")
    def test_asset_admin_get_one_owner_mismatch(self, get_mock):
        get_mock.return_value = SimpleNamespace(id=1, reg_id=2)
        with self.assertRaisesRegex(ValueError, "asset not found"):
            AssetAdminService.get_one(1, 1)

    @patch("app_aibroker.services.asset_admin_service.get_asset_by_id")
    def test_asset_admin_get_one_success(self, get_mock):
        get_mock.return_value = SimpleNamespace(
            id=1, reg_id=1, oss_bucket="b", oss_key="k", content_type=0, ct=1
        )
        d = AssetAdminService.get_one(1, 1)
        self.assertEqual(d["id"], 1)

    @patch("app_aibroker.services.auth_service._get_reg_by_access_key")
    def test_auth_resolve_reg_from_headers(self, get_reg_mock):
        get_reg_mock.return_value = SimpleNamespace(id=1, status=1)
        reg, err = resolve_reg({}, headers={"X-Access-Key": "k"})
        self.assertEqual(err, "")
        self.assertEqual(reg.id, 1)

    @patch("app_aibroker.services.auth_service._get_reg_by_access_key")
    def test_auth_resolve_reg_invalid(self, get_reg_mock):
        get_reg_mock.return_value = None
        reg, err = resolve_reg({"access_key": "k"})
        self.assertIsNone(reg)
        self.assertEqual(err, "invalid access_key")

    def test_auth_resolve_reg_requires_key(self):
        reg, err = resolve_reg({})
        self.assertIsNone(reg)
        self.assertEqual(err, "access_key is required")

    def test_callback_requires_url_and_secret(self):
        ok, status = deliver_callback("", "s", {})
        self.assertFalse(ok)
        self.assertEqual(status, 0)

    @patch("app_aibroker.services.callback_service.request_async")
    def test_callback_async_mode(self, request_async_mock):
        request_async_mock.return_value = "task-1"
        out = deliver_callback("https://cb", "sec", {"x": 1}, async_mode=True)
        self.assertEqual(out, "task-1")

    @patch("app_aibroker.services.callback_service.time.sleep")
    @patch("app_aibroker.services.callback_service.request_sync")
    def test_callback_retry_then_success(self, request_sync_mock, _sleep_mock):
        request_sync_mock.side_effect = [HttpCallError("x"), SimpleNamespace(status_code=200)]
        ok, status = deliver_callback("https://cb", "sec", {"x": 1})
        self.assertTrue(ok)
        self.assertEqual(status, 200)

    @patch("app_aibroker.services.callback_service.time.sleep")
    @patch("app_aibroker.services.callback_service.request_sync")
    def test_callback_returns_false_after_retries(self, request_sync_mock, _sleep_mock):
        request_sync_mock.return_value = SimpleNamespace(status_code=503)
        ok, status = deliver_callback("https://cb", "sec", {"x": 1})
        self.assertFalse(ok)
        self.assertEqual(status, 503)

    @patch("app_aibroker.services.job_service.get_reg_by_id")
    @patch("app_aibroker.services.job_service.deliver_callback")
    @patch("app_aibroker.services.job_service.get_job_by_id")
    @patch("app_aibroker.services.job_service.get_asset_by_id")
    @patch("app_aibroker.services.job_service.update_job")
    @patch("app_aibroker.services.job_service.time.sleep")
    def test_run_job_video_success(
        self, _sleep_mock, update_mock, get_asset_mock, get_job_mock, cb_mock, get_reg_mock
    ):
        job = SimpleNamespace(
            id=9,
            reg_id=1,
            job_type="video_from_image",
            payload_json=json.dumps({"input_asset_id": 5}),
            callback_url="https://cb",
            result_json='{"ok":1}',
            message="",
            status=JOB_DONE,
        )
        get_job_mock.side_effect = [job, job]
        get_asset_mock.return_value = SimpleNamespace(reg_id=1, oss_bucket="b", oss_key="x.jpg")
        get_reg_mock.return_value = SimpleNamespace(callback_secret="secret")

        _run_job(9)

        update_mock.assert_any_call(9, status=JOB_RUNNING)
        update_mock.assert_any_call(9, status=JOB_DONE, result_json=ANY)
        cb_mock.assert_called_once()

    @patch("app_aibroker.services.job_service.get_reg_by_id")
    @patch("app_aibroker.services.job_service.get_job_by_id")
    @patch("app_aibroker.services.job_service.get_asset_by_id")
    @patch("app_aibroker.services.job_service.update_job")
    def test_run_job_invalid_asset_marks_failed(self, update_mock, get_asset_mock, get_job_mock, get_reg_mock):
        job = SimpleNamespace(
            id=10,
            reg_id=1,
            job_type="video_from_image",
            payload_json=json.dumps({"input_asset_id": 7}),
            callback_url="",
            result_json="",
            message="",
            status=JOB_FAILED,
        )
        get_job_mock.side_effect = [job, job]
        get_asset_mock.return_value = None
        get_reg_mock.return_value = None

        _run_job(10)

        update_mock.assert_any_call(10, status=JOB_FAILED, message="invalid input_asset_id")

    @patch("app_aibroker.services.job_service.get_reg_by_id")
    @patch("app_aibroker.services.job_service.get_job_by_id")
    @patch("app_aibroker.services.job_service.update_job")
    def test_run_job_unsupported_type_marks_failed(self, update_mock, get_job_mock, get_reg_mock):
        job = SimpleNamespace(
            id=11,
            reg_id=1,
            job_type="unknown_job",
            payload_json="{}",
            callback_url="",
            result_json="",
            message="",
            status=JOB_FAILED,
        )
        get_job_mock.side_effect = [job, job]
        get_reg_mock.return_value = None
        _run_job(11)
        update_mock.assert_any_call(11, status=JOB_FAILED, message="unsupported job_type: unknown_job")

    @patch("app_aibroker.services.job_service.get_job_by_id")
    def test_run_job_not_found(self, get_job_mock):
        get_job_mock.return_value = None
        _run_job(999)
        get_job_mock.assert_called_once_with(999)

    @patch("app_aibroker.services.job_service.threading.Thread")
    @patch("app_aibroker.services.job_service.create_job")
    def test_enqueue_job(self, create_job_mock, thread_mock):
        create_job_mock.return_value = SimpleNamespace(id=77)
        t = MagicMock()
        thread_mock.return_value = t
        out = enqueue_job(1, "video_from_image", {"a": 1}, "https://cb")
        self.assertEqual(out, {"job_id": 77, "status": JOB_PENDING})
        t.start.assert_called_once()

    def test_job_to_dict(self):
        job = SimpleNamespace(
            id=1,
            reg_id=2,
            job_type="x",
            status=3,
            callback_url="u",
            payload_json='{"a":1}',
            result_json='{"b":2}',
            message="m",
            ct=11,
            ut=22,
        )
        d = job_to_dict(job)
        self.assertEqual(d["payload_json"], {"a": 1})
        self.assertEqual(d["result_json"], {"b": 2})

    @patch("app_aibroker.services.metrics_service.get_now_timestamp_ms")
    @patch("app_aibroker.services.metrics_service.AiCallLog")
    def test_metrics_summary_since(self, model_mock, now_ms_mock):
        now_ms_mock.return_value = 10000
        qs = MagicMock()
        model_mock.objects.using.return_value.filter.return_value = qs
        qs.filter.return_value = qs
        qs.aggregate.return_value = {"total": 4, "success": 3, "fail": 1, "avg_latency": 25.5}
        out = summary_since(reg_id=9, window_ms=5000)
        self.assertEqual(out["total_calls"], 4)
        self.assertEqual(out["success_rate"], 0.75)
        qs.filter.assert_called_once_with(reg_id=9)

    @patch("app_aibroker.services.metrics_service.get_now_timestamp_ms")
    @patch("app_aibroker.services.metrics_service.AiCallLog")
    def test_metrics_summary_since_zero_total(self, model_mock, now_ms_mock):
        now_ms_mock.return_value = 10000
        qs = MagicMock()
        model_mock.objects.using.return_value.filter.return_value = qs
        qs.aggregate.return_value = {"total": 0, "success": 0, "fail": 0, "avg_latency": None}
        out = summary_since(reg_id=None, window_ms=5000)
        self.assertEqual(out["total_calls"], 0)
        self.assertEqual(out["success_rate"], 0.0)

    @patch("app_aibroker.services.reg_service.create_reg")
    def test_reg_service_create_and_list(self, create_reg_mock):
        create_reg_mock.return_value = SimpleNamespace(
            id=1,
            name="demo",
            status=1,
            access_key="abcdefgh123",
            callback_secret="secret",
            ct=1,
            ut=2,
        )
        d = RegService.create_by_payload({"name": " demo ", "status": 1})
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["access_key"], "abcdefgh123")

    @patch("app_aibroker.services.reg_service.list_regs")
    def test_reg_service_list_and_console(self, list_regs_mock):
        list_regs_mock.return_value = [
            SimpleNamespace(id=1, name="n", status=1, access_key="abcdefgh123", ct=1, ut=2)
        ]
        d1 = RegService.list_all()
        d2 = RegService.list_all_for_console()
        self.assertTrue(d1[0]["access_key"].startswith("abcdefgh"))
        self.assertEqual(d2[0]["access_key"], "abcdefgh123")

    @patch("app_aibroker.services.reg_service.get_reg_by_id")
    def test_reg_service_get_one_not_found(self, get_mock):
        get_mock.return_value = None
        with self.assertRaisesRegex(ValueError, "reg not found"):
            RegService.get_one(1)

    def test_reg_service_create_requires_name(self):
        with self.assertRaisesRegex(ValueError, "name is required"):
            RegService.create_by_payload({"name": "  "})

    @patch("app_aibroker.services.reg_service.update_reg")
    @patch("app_aibroker.services.reg_service.delete_reg")
    def test_reg_service_update_delete(self, delete_mock, update_mock):
        update_mock.return_value = SimpleNamespace(
            id=1, name="x", status=1, access_key="abcdefgh123", ct=1, ut=2
        )
        delete_mock.return_value = True
        d = RegService.update_by_payload(1, {"name": "x", "status": 1})
        ok = RegService.delete(1)
        self.assertEqual(d["id"], 1)
        self.assertTrue(ok)

    @patch("app_aibroker.services.reg_service.update_reg")
    @patch("app_aibroker.services.reg_service.delete_reg")
    def test_reg_service_update_delete_not_found(self, delete_mock, update_mock):
        update_mock.return_value = None
        delete_mock.return_value = False
        with self.assertRaisesRegex(ValueError, "reg not found"):
            RegService.update_by_payload(1, {"name": "x"})
        with self.assertRaisesRegex(ValueError, "reg not found"):
            RegService.delete(1)

    @patch("app_aibroker.services.template_admin_service.create_template")
    def test_template_admin_create(self, create_mock):
        create_mock.return_value = SimpleNamespace(
            id=1,
            template_key="k",
            constraint_type=0,
            description="d",
            body="b",
            param_specs="[]",
            resp_specs="[]",
            status=1,
            ct=1,
            ut=2,
        )
        d = TemplateAdminService.create_by_payload({"template_key": " k ", "body": " b "})
        self.assertEqual(d["template_key"], "k")
        self.assertEqual(d["body"], "b")

    def test_template_admin_create_invalid(self):
        with self.assertRaisesRegex(ValueError, "required"):
            TemplateAdminService.create_by_payload({"template_key": "", "body": ""})

    @patch("app_aibroker.services.template_admin_service.list_templates")
    @patch("app_aibroker.services.template_admin_service.get_template")
    @patch("app_aibroker.services.template_admin_service.update_template")
    @patch("app_aibroker.services.template_admin_service.delete_template")
    def test_template_admin_list_get_update_delete(
        self, delete_mock, update_mock, get_mock, list_mock
    ):
        t = SimpleNamespace(
            id=1,
            template_key="k",
            constraint_type=0,
            description="d",
            body="b",
            param_specs="[]",
            resp_specs="[]",
            status=1,
            ct=1,
            ut=2,
        )
        list_mock.return_value = [t]
        get_mock.return_value = t
        update_mock.return_value = t
        delete_mock.return_value = True
        self.assertEqual(len(TemplateAdminService.list_all("k")), 1)
        self.assertEqual(TemplateAdminService.get_one(1)["id"], 1)
        self.assertEqual(TemplateAdminService.update_by_payload(1, {"status": 1})["id"], 1)
        self.assertTrue(TemplateAdminService.delete(1))

    @patch("app_aibroker.services.template_admin_service.get_template")
    @patch("app_aibroker.services.template_admin_service.update_template")
    @patch("app_aibroker.services.template_admin_service.delete_template")
    def test_template_admin_not_found_branches(self, delete_mock, update_mock, get_mock):
        get_mock.return_value = None
        update_mock.return_value = None
        delete_mock.return_value = False
        with self.assertRaisesRegex(ValueError, "template not found"):
            TemplateAdminService.get_one(1)
        with self.assertRaisesRegex(ValueError, "template not found"):
            TemplateAdminService.update_by_payload(1, {"status": 1})
        with self.assertRaisesRegex(ValueError, "template not found"):
            TemplateAdminService.delete(1)
