"""CMS console views (content types and per-type rows)."""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services import (
    ConsoleContentReadService,
    ContentModelResolver,
    ContentPayloadSerializer,
    ContentWriteService,
)
from app_cms.services.content_physical_table_service import ContentPhysicalTableService
from app_cms.validation import (
    merge_json_string_fields,
    parse_content_meta_fields_from_post,
    validate_item_payload,
    validate_store_meta,
    validate_update_meta,
)


def _cms_per_page() -> int:
    return min(
        max(1, int(getattr(settings, "CMS_LIST_PER_PAGE", 15))),
        int(getattr(settings, "CMS_LIST_PER_PAGE_MAX", 50)),
    )


def _cms_content_list_back(request) -> tuple[str, str, str]:
    """List page back link: content-data tab vs content-meta index (see ?from=)."""
    from_param = (request.GET.get("from") or "").strip().lower()
    if from_param == "meta":
        return (
            reverse("console:cms-content-meta-index"),
            "返回内容类型",
            "meta",
        )
    return (
        reverse("console:cms-dashboard") + "?tab=content#cms-type-rows",
        "返回内容数据",
        "dashboard",
    )


@method_decorator(csrf_protect, name="dispatch")
class CmsDashboardView(View):
    def get(self, request, *args, **kwargs):
        resolver = ContentModelResolver()
        rows = []
        for meta in CmsContentMeta.objects.order_by("name"):
            cls = resolver.model_class(meta)
            rows.append({"meta": meta, "count": cls.objects.count()})
        subnav_active = (
            "content" if (request.GET.get("tab") == "content") else "dashboard"
        )
        return render(
            request,
            "console/cms/dashboard.html",
            {"type_stats": rows, "cms_subnav_active": subnav_active},
        )


@method_decorator(csrf_protect, name="dispatch")
class CmsContentMetaIndexView(View):
    """GET list, POST create (same path as Laravel resource)."""

    def get(self, request, *args, **kwargs):
        items = CmsContentMeta.objects.order_by("name")
        return render(request, "console/cms/content_meta_list.html", {"items": items})

    def post(self, request, *args, **kwargs):
        name = (request.POST.get("name") or "").strip()
        try:
            fields = parse_content_meta_fields_from_post(request.POST)
            payload = validate_store_meta(
                name=name,
                fields=fields,
            )
            meta = CmsContentMeta.objects.create(
                name=payload["name"],
                fields=payload["fields"],
            )
            try:
                ContentPhysicalTableService().ensure_table(meta)
            except ValueError as exc:
                meta.delete()
                raise ValidationError({"fields": str(exc)}) from exc
            except Exception:
                meta.delete()
                raise
        except ValidationError as e:
            for k, msg in (e.message_dict or {}).items():
                messages.error(request, f"{k}: {msg}")
            return HttpResponseRedirect(reverse("console:cms-content-meta-create"))
        messages.success(request, "Content type registered.")
        return HttpResponseRedirect(reverse("console:cms-content-meta-index"))


@method_decorator(csrf_protect, name="dispatch")
class CmsContentMetaCreateView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "console/cms/content_meta_edit.html", {})


@method_decorator(csrf_protect, name="dispatch")
class CmsContentMetaEditView(View):
    def get(self, request, pk: int, *args, **kwargs):
        meta = CmsContentMeta.objects.filter(pk=pk).first()
        if meta is None:
            raise Http404()
        return render(
            request,
            "console/cms/content_meta_edit.html",
            {"meta": meta, "columns_json": meta.fields},
        )

    def post(self, request, pk: int, *args, **kwargs):
        meta = CmsContentMeta.objects.filter(pk=pk).first()
        if meta is None:
            raise Http404()
        try:
            fields = parse_content_meta_fields_from_post(request.POST)
            payload = validate_update_meta(fields=fields)
            old_fields = meta.fields
            meta.fields = payload["fields"]
            try:
                ContentPhysicalTableService().sync_schema(meta, previous_fields=old_fields)
            except (ValueError, DatabaseError) as exc:
                meta.fields = old_fields
                messages.error(request, str(exc))
                return HttpResponseRedirect(reverse("console:cms-content-meta-edit", kwargs={"pk": pk}))
            meta.save()
        except ValidationError as e:
            for k, msg in (e.message_dict or {}).items():
                messages.error(request, f"{k}: {msg}")
            return HttpResponseRedirect(reverse("console:cms-content-meta-edit", kwargs={"pk": pk}))
        messages.success(request, "Content type updated.")
        return HttpResponseRedirect(reverse("console:cms-content-meta-index"))


@method_decorator(csrf_protect, name="dispatch")
class CmsContentMetaDeleteView(View):
    def post(self, request, pk: int, *args, **kwargs):
        meta = CmsContentMeta.objects.filter(pk=pk).first()
        if meta is None:
            raise Http404()
        meta.delete()
        messages.success(request, "Content type removed and backing table dropped if present.")
        return HttpResponseRedirect(reverse("console:cms-content-meta-index"))


@method_decorator(csrf_protect, name="dispatch")
class CmsContentItemListView(View):
    """GET list, POST create."""

    def get(self, request, content_route: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        page = max(1, int(request.GET.get("page") or 1))
        paginator = ConsoleContentReadService().paginate_all(meta, page, _cms_per_page())
        serializer = ContentPayloadSerializer()
        items = [serializer.list_item(meta, m) for m in paginator.object_list]
        back_url, back_label, cms_back_from = _cms_content_list_back(request)
        return render(
            request,
            "console/cms/content_list.html",
            {
                "meta": meta,
                "items": items,
                "page_obj": paginator,
                "cms_back_url": back_url,
                "cms_back_label": back_label,
                "cms_back_from": cms_back_from,
            },
        )

    def post(self, request, content_route: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        raw = request.POST.copy()
        raw = merge_json_string_fields(meta, raw)
        try:
            cleaned = validate_item_payload(meta, raw, partial=False)
            ContentWriteService().store(meta, cleaned)
        except ValidationError as e:
            for k, msg in (e.message_dict or {}).items():
                messages.error(request, f"{k}: {msg}")
            return HttpResponseRedirect(
                reverse("console:cms-content-create", kwargs={"content_route": meta.route_segment()})
            )
        messages.success(request, "Record created.")
        return HttpResponseRedirect(
            reverse("console:cms-content-index", kwargs={"content_route": meta.route_segment()})
        )


@method_decorator(csrf_protect, name="dispatch")
class CmsContentItemCreateView(View):
    def get(self, request, content_route: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        return render(request, "console/cms/content_edit.html", {"meta": meta})


@method_decorator(csrf_protect, name="dispatch")
class CmsContentItemEditView(View):
    def get(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        resolver = ContentModelResolver()
        cls = resolver.model_class(meta)
        try:
            rid = int(record_id)
        except ValueError as e:
            raise Http404() from e
        model = cls.objects.filter(pk=rid).first()
        if model is None:
            raise Http404()
        return render(
            request,
            "console/cms/content_edit.html",
            {"meta": meta, "model": model},
        )

    def post(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            rid = int(record_id)
        except ValueError as e:
            raise Http404() from e
        raw = request.POST.copy()
        raw = merge_json_string_fields(meta, raw)
        try:
            cleaned = validate_item_payload(meta, raw, partial=True)
            ContentWriteService().update(meta, rid, cleaned)
        except ValidationError as e:
            for k, msg in (e.message_dict or {}).items():
                messages.error(request, f"{k}: {msg}")
            return HttpResponseRedirect(
                reverse(
                    "console:cms-content-edit",
                    kwargs={"content_route": meta.route_segment(), "record_id": record_id},
                )
            )
        except Http404:
            raise
        messages.success(request, "Record updated.")
        return HttpResponseRedirect(
            reverse("console:cms-content-index", kwargs={"content_route": meta.route_segment()})
        )


@method_decorator(csrf_protect, name="dispatch")
class CmsContentItemDeleteView(View):
    def post(self, request, content_route: str, record_id: str, *args, **kwargs):
        meta = CmsContentMeta.find_by_route_segment(content_route)
        if meta is None:
            raise Http404()
        try:
            rid = int(record_id)
        except ValueError as e:
            raise Http404() from e
        try:
            ContentWriteService().destroy(meta, rid)
        except Http404:
            raise
        messages.success(request, "Record deleted.")
        return HttpResponseRedirect(
            reverse("console:cms-content-index", kwargs={"content_route": meta.route_segment()})
        )
