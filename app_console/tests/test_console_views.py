from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings

from app_console.views.cdn_view import CdnDistributionDetailView, CdnDistributionListView
from app_console.views.dashboard_view import DashboardView
from app_console.views.know_view import KnowPointDetailView
from app_console.views.searchrec_view import SearchRecConsoleView


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

    @override_settings(APP_SEARCHREC_ENABLED=True)
    def test_searchrec_console_context(self):
        view = SearchRecConsoleView()
        context = view.get_context_data()
        self.assertTrue(context["searchrec_enabled"])
        self.assertEqual(context["searchrec_api_base"], "/api/searchrec")

    def test_know_point_detail_invalid_id(self):
        request = self.factory.get("/console/know/points/0/")
        with self.assertRaises(Http404):
            KnowPointDetailView.as_view()(request, point_id=0)
