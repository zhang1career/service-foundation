from __future__ import annotations

from django.conf import settings
from rest_framework.views import APIView

from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import post_payload, resp_err, resp_ok, response_with_request_id

from app_textmod.enums.lexicon_biz_type_enum import coerce_lexicon_biz_type_id
from app_textmod.repos.lexicon_repo import add_entries, create_lexicon, get_lexicon, list_lexicons
from app_textmod.services.lexicon_publish_service import LexiconPublishService


class LexiconListCreateView(APIView):
    def get(self, request, *args, **kwargs):
        rows = list_lexicons()
        data = [
            {"id": int(r.id), "name": r.name, "biz_type": int(r.biz_type), "ct": int(r.ct), "ut": int(r.ut)}
            for r in rows
        ]
        return response_with_request_id(request, resp_ok({"items": data}))

    def post(self, request, *args, **kwargs):
        data = post_payload(request) or {}
        try:
            bt = coerce_lexicon_biz_type_id(data.get("biz_type"))
            lex = create_lexicon(name=str(data.get("name", "")), biz_type=bt)
            return response_with_request_id(
                request,
                resp_ok({"id": int(lex.id), "name": lex.name, "biz_type": int(lex.biz_type)}),
            )
        except ValueError as exc:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message=str(exc)),
            )


class LexiconEntriesCreateView(APIView):
    def post(self, request, *args, **kwargs):
        lexicon_id = int(kwargs.get("lexicon_id") or 0)
        if lexicon_id <= 0:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="invalid lexicon_id"),
            )
        if get_lexicon(lexicon_id) is None:
            return response_with_request_id(
                request,
                resp_err(code=RET_RESOURCE_NOT_FOUND, message="lexicon not found"),
            )
        data = post_payload(request) or {}
        entries = data.get("entries")
        if not isinstance(entries, list):
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="entries must be a list"),
            )
        try:
            n = add_entries(
                lexicon_id=lexicon_id,
                entries=entries,
                batch_max=int(settings.TEXTMOD_ENTRY_BATCH_MAX),
            )
            return response_with_request_id(request, resp_ok({"inserted": n}))
        except ValueError as exc:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message=str(exc)),
            )


class LexiconPublishView(APIView):
    def post(self, request, *args, **kwargs):
        lexicon_id = int(kwargs.get("lexicon_id") or 0)
        if lexicon_id <= 0:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="invalid lexicon_id"),
            )
        if get_lexicon(lexicon_id) is None:
            return response_with_request_id(
                request,
                resp_err(code=RET_RESOURCE_NOT_FOUND, message="lexicon not found"),
            )
        try:
            ver = LexiconPublishService.publish(lexicon_id)
            return response_with_request_id(
                request,
                resp_ok(
                    {
                        "lexicon_version_id": int(ver.id),
                        "seq": int(ver.seq),
                        "entry_count": int(ver.entry_count),
                        "blob_checksum": ver.blob_checksum,
                    }
                ),
            )
        except ValueError as exc:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message=str(exc)),
            )
