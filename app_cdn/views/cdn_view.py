"""
CDN REST API views - CloudFront-compatible interface

API paths follow CloudFront REST API structure:
- GET    /distribution              -> ListDistributions
- POST   /distribution              -> CreateDistribution
- GET    /distribution/{id}         -> GetDistribution
- DELETE /distribution/{id}         -> DeleteDistribution
- GET    /distribution/{id}/config  -> GetDistributionConfig
- PUT    /distribution/{id}/config  -> UpdateDistribution
- POST   /distribution/{id}/invalidation -> CreateInvalidation
- GET    /distribution/{id}/invalidation -> ListInvalidations
- GET    /distribution/{id}/invalidation/{inv_id} -> GetInvalidation
"""
import logging
from rest_framework import status as http_status
from rest_framework.views import APIView

from app_cdn.exceptions.not_found_exception import DistributionNotFoundException
from app_cdn.services.cdn_service import CdnService
from common.utils.http_util import resp_err, resp_exception, resp_ok

logger = logging.getLogger(__name__)


class DistributionListView(APIView):
    """List and create distributions"""

    def get(self, request, *args, **kwargs):
        """ListDistributions - GET /distribution"""
        try:
            marker = request.GET.get("Marker") or None
            max_items = request.GET.get("MaxItems")
            max_items = int(max_items) if max_items else None

            service = CdnService()
            result = service.list_distributions(marker=marker, max_items=max_items)
            return resp_ok(result)
        except Exception as e:
            logger.exception("[DistributionListView.get] %s", e)
            return resp_exception(e)

    def post(self, request, *args, **kwargs):
        """CreateDistribution - POST /distribution"""
        try:
            data = request.data if hasattr(request, "data") else {}
            if not data:
                return resp_err("Request body required", status=http_status.HTTP_400_BAD_REQUEST)

            service = CdnService()
            result = service.create_distribution(data)
            return resp_ok(result, status=http_status.HTTP_201_CREATED)
        except ValueError as e:
            return resp_err(str(e), status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("[DistributionListView.post] %s", e)
            return resp_exception(e)


class DistributionDetailView(APIView):
    """Get and delete distribution"""

    def get(self, request, distribution_id, *args, **kwargs):
        """GetDistribution - GET /distribution/{id}"""
        try:
            service = CdnService()
            result = service.get_distribution(distribution_id)
            if not result:
                return resp_err(
                    "NoSuchDistribution",
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            return resp_ok({"Distribution": result})
        except Exception as e:
            logger.exception("[DistributionDetailView.get] %s", e)
            return resp_exception(e)

    def delete(self, request, distribution_id, *args, **kwargs):
        """DeleteDistribution - DELETE /distribution/{id}"""
        try:
            if_match = request.headers.get("If-Match")
            service = CdnService()
            success = service.delete_distribution(distribution_id, if_match=if_match)
            if not success:
                return resp_err(
                    "NoSuchDistribution",
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            return resp_ok({"message": "Distribution deleted"})
        except ValueError as e:
            if "PreconditionFailed" in str(e):
                return resp_err(str(e), status=http_status.HTTP_412_PRECONDITION_FAILED)
            return resp_err(str(e), status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("[DistributionDetailView.delete] %s", e)
            return resp_exception(e)


class DistributionConfigView(APIView):
    """Get and update distribution config"""

    def get(self, request, distribution_id, *args, **kwargs):
        """GetDistributionConfig - GET /distribution/{id}/config"""
        try:
            service = CdnService()
            result = service.get_distribution_config(distribution_id)
            if not result:
                return resp_err(
                    "NoSuchDistribution",
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            return resp_ok({"DistributionConfig": result})
        except Exception as e:
            logger.exception("[DistributionConfigView.get] %s", e)
            return resp_exception(e)

    def put(self, request, distribution_id, *args, **kwargs):
        """UpdateDistribution - PUT /distribution/{id}/config"""
        try:
            data = request.data if hasattr(request, "data") else {}
            if not data:
                return resp_err("Request body required", status=http_status.HTTP_400_BAD_REQUEST)

            if_match = request.headers.get("If-Match")
            service = CdnService()
            result = service.update_distribution(
                distribution_id, data, if_match=if_match
            )
            if not result:
                return resp_err(
                    "NoSuchDistribution",
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            return resp_ok(result)
        except ValueError as e:
            if "PreconditionFailed" in str(e):
                return resp_err(str(e), status=http_status.HTTP_412_PRECONDITION_FAILED)
            return resp_err(str(e), status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("[DistributionConfigView.put] %s", e)
            return resp_exception(e)


class InvalidationListView(APIView):
    """List and create invalidations"""

    def get(self, request, distribution_id, *args, **kwargs):
        """ListInvalidations - GET /distribution/{id}/invalidation"""
        try:
            marker = request.GET.get("Marker") or None
            max_items = request.GET.get("MaxItems")
            max_items = int(max_items) if max_items else None

            service = CdnService()
            result = service.list_invalidations(
                distribution_id, marker=marker, max_items=max_items
            )
            return resp_ok(result)
        except DistributionNotFoundException:
            return resp_err(
                "NoSuchDistribution",
                status=http_status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("[InvalidationListView.get] %s", e)
            return resp_exception(e)

    def post(self, request, distribution_id, *args, **kwargs):
        """CreateInvalidation - POST /distribution/{id}/invalidation"""
        try:
            data = request.data if hasattr(request, "data") else {}
            if not data:
                return resp_err("Request body required", status=http_status.HTTP_400_BAD_REQUEST)

            batch = data.get("InvalidationBatch", data)
            caller_ref = batch.get("CallerReference", "")
            paths_obj = batch.get("Paths", {})
            paths = paths_obj.get("Items", paths_obj.get("paths", ["/*"]))
            if not isinstance(paths, list):
                paths = ["/*"]

            if not caller_ref:
                return resp_err("CallerReference is required", status=http_status.HTTP_400_BAD_REQUEST)

            service = CdnService()
            result = service.create_invalidation(
                distribution_id, paths=paths, caller_reference=caller_ref
            )
            return resp_ok(result, status=http_status.HTTP_201_CREATED)
        except DistributionNotFoundException:
            return resp_err(
                "NoSuchDistribution",
                status=http_status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("[InvalidationListView.post] %s", e)
            return resp_exception(e)


class InvalidationDetailView(APIView):
    """Get invalidation"""

    def get(self, request, distribution_id, invalidation_id, *args, **kwargs):
        """GetInvalidation - GET /distribution/{id}/invalidation/{inv_id}"""
        try:
            service = CdnService()
            result = service.get_invalidation(distribution_id, invalidation_id)
            if not result:
                return resp_err(
                    "NoSuchInvalidation",
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            return resp_ok(result)
        except Exception as e:
            logger.exception("[InvalidationDetailView.get] %s", e)
            return resp_exception(e)
