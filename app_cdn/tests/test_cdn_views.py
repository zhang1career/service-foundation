import json
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from app_cdn.views.cdn_view import DistributionDetailView, DistributionListView, InvalidationListView
from app_cdn.views.content_delivery_view import ContentDeliveryView
from common.consts.response_const import RET_OK


class CdnViewsFunctionalTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_cdn.views.cdn_view.CdnService")
    def test_distribution_list_success(self, service_cls):
        service_cls.return_value.list_distributions.return_value = {"Items": [], "Quantity": 0}
        request = self.factory.get("/api/cdn/2020-05-31/distribution")
        response = DistributionListView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)

    def test_distribution_create_missing_body(self):
        request = self.factory.post("/api/cdn/2020-05-31/distribution", data={}, format="json")
        response = DistributionListView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("required", payload["message"])

    @patch("app_cdn.views.cdn_view.CdnService")
    def test_distribution_detail_not_found(self, service_cls):
        service_cls.return_value.get_distribution.return_value = None
        request = self.factory.get("/api/cdn/2020-05-31/distribution/d-1")
        response = DistributionDetailView.as_view()(request, distribution_id="d-1")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(payload["message"], "NoSuchDistribution")

    @patch("app_cdn.views.cdn_view.CdnService")
    def test_invalidation_create_missing_caller_reference(self, service_cls):
        service_cls.return_value.create_invalidation.return_value = {"id": "i-1"}
        request = self.factory.post(
            "/api/cdn/2020-05-31/distribution/d-1/invalidation",
            data={"InvalidationBatch": {"Paths": {"Items": ["/*"]}}},
            format="json",
        )
        response = InvalidationListView.as_view()(request, distribution_id="d-1")
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("CallerReference", payload["message"])

    @patch("app_cdn.views.content_delivery_view.put_to_cache")
    @patch("app_cdn.views.content_delivery_view.fetch_from_origin")
    @patch("app_cdn.views.content_delivery_view.get_from_cache")
    @patch("app_cdn.views.content_delivery_view.build_origin_base_url")
    @patch("app_cdn.views.content_delivery_view.get_distribution_by_id")
    def test_content_delivery_cache_miss_then_origin_success(
            self,
            get_distribution_mock,
            build_origin_mock,
            get_cache_mock,
            fetch_origin_mock,
            put_cache_mock,
    ):
        class Dist:
            id = 3
            enabled = True

            @staticmethod
            def get_origin_config():
                return {"Origins": {"Items": [{"DomainName": "example.com"}]}}

        get_distribution_mock.return_value = Dist()
        build_origin_mock.return_value = "https://example.com"
        get_cache_mock.return_value = None
        fetch_origin_mock.return_value = (b"hello", "text/plain", 200, "https://example.com/a.txt")

        request = self.factory.get("/api/cdn/2020-05-31/d/3/a.txt")
        response = ContentDeliveryView.as_view()(request, distribution_id="3", path="a.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Cache"], "MISS")
        put_cache_mock.assert_called_once()
