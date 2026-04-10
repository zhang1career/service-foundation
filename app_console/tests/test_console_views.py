import json

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings

from app_console.utils import embed_dict_as_json_script_body
from app_console.views.cdn_view import CdnDistributionDetailView, CdnDistributionListView
from app_console.views.dashboard_view import DashboardView
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
    def test_dashboard_context_contains_app_flags(self):
        view = DashboardView()
        context = view.get_context_data()
        self.assertTrue(context["apps"]["cdn"]["enabled"])
        self.assertFalse(context["apps"]["searchrec"]["enabled"])

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
