import json
from unittest.mock import patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings

from app_console.utils import embed_dict_as_json_script_body
from app_console.views.cdn_view import CdnDistributionDetailView, CdnDistributionListView
from app_console.views.dashboard_view import DashboardView
from app_console.views.monitoring_api_view import MonitoringJsonView, MonitoringSnapshotView
from app_console.views.know_view import KnowPointDetailView
from app_console.views.searchrec_view import SearchRecConsoleView


class EmbedJsonScriptBodyTest(SimpleTestCase):
    def test_object_array_like_nested_braces_round_trip(self):
        inner = (
            '[{"n":"messages","t":"OBJECT_ARRAY","r":{},'
            '"c":[{"n":"role","t":"STRING","r":{}}]}]'
        )
        blob = embed_dict_as_json_script_body({"42": inner})
        parsed = json.loads(str(blob))
        self.assertEqual(parsed["42"], inner)

    def test_escapes_angle_brackets_for_script_context(self):
        raw = "</script><script>evil"
        blob = embed_dict_as_json_script_body({"1": raw})
        wire = str(blob)
        self.assertNotIn("<script>", wire)
        self.assertEqual(json.loads(wire)["1"], raw)


class ConsoleViewsFunctionalTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(APP_CDN_ENABLED=True, APP_SEARCHREC_ENABLED=False)
    def test_dashboard_context_has_apps_config_json(self):
        view = DashboardView()
        context = view.get_context_data()
        cfg = json.loads(context["apps_config_json"])
        cdn = next(x for x in cfg if x["key"] == "cdn")
        self.assertTrue(cdn["enabled"])
        sr = next(x for x in cfg if x["key"] == "searchrec")
        self.assertFalse(sr["enabled"])
        kc = next(x for x in cfg if x["key"] == "keepcon")
        self.assertFalse(kc["enabled"])
        self.assertIn("monitoring_refresh_ms", context)

    @override_settings(APP_CDN_ENABLED=True, APP_KEEPCON_ENABLED=True)
    def test_dashboard_includes_keepcon_when_enabled(self):
        view = DashboardView()
        context = view.get_context_data()
        cfg = json.loads(context["apps_config_json"])
        kc = next(x for x in cfg if x["key"] == "keepcon")
        self.assertTrue(kc["enabled"])
        self.assertEqual(kc["httpProbeKey"], "keepcon_health")

    @override_settings(APP_CDN_ENABLED=True)
    def test_cdn_console_context(self):
        list_view = CdnDistributionListView()
        list_context = list_view.get_context_data()
        self.assertTrue(list_context["cdn_enabled"])
        self.assertEqual(list_context["cdn_api_base"], "/api/cdn/2020-05-31")

        detail_view = CdnDistributionDetailView()
        detail_context = detail_view.get_context_data(distribution_id="dist-1")
        self.assertEqual(detail_context["distribution_id"], "dist-1")

    @override_settings(APP_SEARCHREC_ENABLED=True, CONSOLE_SEARCHREC_ACCESS_KEY="")
    def test_searchrec_console_context(self):
        view = SearchRecConsoleView()
        context = view.get_context_data()
        self.assertTrue(context["searchrec_enabled"])
        self.assertEqual(context["searchrec_api_base"], "/api/searchrec")
        self.assertEqual(
            json.loads(context["searchrec_examples"]["upsert"])["access_key"],
            "",
        )

    @override_settings(APP_SEARCHREC_ENABLED=True, CONSOLE_SEARCHREC_ACCESS_KEY="ak_test_1")
    def test_searchrec_console_examples_follow_access_key_setting(self):
        view = SearchRecConsoleView()
        context = view.get_context_data()
        self.assertEqual(
            json.loads(context["searchrec_examples"]["upsert"])["access_key"],
            "ak_test_1",
        )

    def test_know_point_detail_invalid_id(self):
        request = self.factory.get("/console/know/points/0/")
        with self.assertRaises(Http404):
            KnowPointDetailView.as_view()(request, point_id=0)

    @override_settings(CONSOLE_MONITORING_JSON_TOKEN="")
    def test_monitoring_json_forbidden_when_token_unconfigured(self):
        request = self.factory.get("/console/api/monitoring.json")
        response = MonitoringJsonView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    @override_settings(CONSOLE_MONITORING_JSON_TOKEN="secret-token")
    def test_monitoring_json_forbidden_when_token_wrong(self):
        request = self.factory.get("/console/api/monitoring.json?token=bad")
        response = MonitoringJsonView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    @override_settings(CONSOLE_MONITORING_JSON_TOKEN="secret-token")
    @patch("app_console.views.monitoring_api_view.get_snapshot_payload")
    def test_monitoring_json_ok_with_query_token(self, snap_mock):
        snap_mock.return_value = {"collected_at": "t"}
        request = self.factory.get("/console/api/monitoring.json?token=secret-token")
        response = MonitoringJsonView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode())["collected_at"], "t")

    @override_settings(CONSOLE_MONITORING_JSON_TOKEN="secret-token")
    @patch("app_console.views.monitoring_api_view.get_snapshot_payload")
    def test_monitoring_json_ok_with_header_token(self, snap_mock):
        snap_mock.return_value = {"ok": True}
        request = self.factory.get(
            "/console/api/monitoring.json",
            HTTP_X_CONSOLE_MONITORING_TOKEN="secret-token",
        )
        response = MonitoringJsonView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    @patch("app_console.views.monitoring_api_view.get_snapshot_payload")
    def test_monitoring_snapshot_returns_json(self, snap_mock):
        snap_mock.return_value = {"collected_at": "t0", "mysql": {}}
        request = self.factory.get("/console/api/monitoring/snapshot/")
        response = MonitoringSnapshotView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode())["collected_at"], "t0")
