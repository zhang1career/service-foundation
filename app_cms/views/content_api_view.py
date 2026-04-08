from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_payload_serializer import ContentPayloadSerializer
from app_cms.services.content_read_service import ContentReadService
from app_cms.services.content_write_service import ContentWriteService
from app_cms.validation.content_field_rules import validate_item_payload
from common.utils.django_util import post_like_mapping_to_dict
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err


def _request_post_like_mapping(request) -> dict[str, Any]:
    payload = request.data if hasattr(request, "data") else request.POST
    return post_like_mapping_to_dict(payload)


def _validation_error_response(e: ValidationError):
    err_data = getattr(e, "message_dict", None)
    return resp_err(
        data=err_data,
        code=RET_INVALID_PARAM,
        message=str(e),
    )


def _list_per_page() -> int:
    return int(getattr(settings, "CMS_LIST_PER_PAGE", 15))


def _list_per_page_max() -> int:
    return int(getattr(settings, "CMS_LIST_PER_PAGE_MAX", 50))


class CmsContentListApiView(APIView):
    def get(self, request, content_route: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        page = max(1, int(request.query_params.get("page") or 1))
        max_pp = _list_per_page_max()
        default_pp = _list_per_page()
        per_page = max(1, int(request.query_params.get("per_page") or default_pp))
        per_page = min(per_page, max_pp)
        svc = ContentReadService()
        page_obj = svc.paginate_published(meta, page, per_page)
        items = [svc.list_item_array(meta, m) for m in page_obj.object_list]
        return resp_ok(
            {
                "items": items,
                "pagination": {
                    "total": page_obj.paginator.count,
                    "per_page": page_obj.paginator.per_page,
                    "current_page": page_obj.number,
                    "last_page": page_obj.paginator.num_pages,
                },
            }
        )

    def post(self, request, content_route: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            cleaned = validate_item_payload(meta, _request_post_like_mapping(request), partial=False)
            model = ContentWriteService().store(meta, cleaned)
            data = ContentPayloadSerializer().detail(meta, model)
            return resp_ok(data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return _validation_error_response(e)


class CmsContentDetailApiView(APIView):
    def get(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            data = ContentReadService().detail_by_pk(meta, int(record_id))
            return resp_ok(data)
        except Http404:
            raise

    def put(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            cleaned = validate_item_payload(meta, _request_post_like_mapping(request), partial=True)
            model = ContentWriteService().update(meta, int(record_id), cleaned)
            data = ContentPayloadSerializer().detail(meta, model)
            return resp_ok(data)
        except ValidationError as e:
            return _validation_error_response(e)
        except Http404:
            raise

    def delete(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            ContentWriteService().destroy(meta, int(record_id))
            return resp_ok("")
        except Http404:
            raise
