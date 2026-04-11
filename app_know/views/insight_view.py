"""
Insight REST API: CRUD + generate insights.
"""
import logging

from rest_framework.views import APIView

from app_know.repos import insight_repo
from app_know.services.insight_agent import generate_insights_and_store
from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _to_dict(i):
    return {
        "id": i.id,
        "content": i.content,
        "type": i.type,
        "status": i.status,
        "perspective": i.perspective,
        "ct": i.ct,
        "ut": i.ut,
    }


class InsightListView(APIView):
    """GET: list insights. POST: create insight."""

    def get(self, request):
        """List insights. Query: perspective, type, status, offset, limit."""
        try:
            perspective = request.GET.get("perspective") or request.GET.get("pid")
            if perspective is not None and perspective != "":
                try:
                    perspective = int(perspective)
                except (TypeError, ValueError):
                    perspective = None
            itype = request.GET.get("type")
            if itype is not None and itype != "":
                try:
                    itype = int(itype)
                except (TypeError, ValueError):
                    itype = None
            status = request.GET.get("status")
            if status is not None and status != "":
                try:
                    status = int(status)
                except (TypeError, ValueError):
                    status = None
            offset = int(request.GET.get("offset") or 0)
            limit = int(request.GET.get("limit") or 100)
            items, total = insight_repo.list_insights(
                perspective=perspective, type=itype, status=status,
                offset=offset, limit=limit,
            )
            return resp_ok({
                "data": [_to_dict(i) for i in items],
                "total_num": total,
                "next_offset": offset + len(items) if (offset + len(items)) < total else None,
            })
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[InsightListView] Error: %s", e)
            return resp_exception(e)

    def post(self, request):
        """Create insight. Body: content (required), type (int), status (int), perspective."""
        try:
            data = getattr(request, "data", None) or request.POST or {}
            content = (data.get("content") or "").strip()
            try:
                itype = int(data.get("type")) if data.get("type") not in (None, "") else 1
            except (TypeError, ValueError):
                itype = 1
            status = data.get("status", 0)
            try:
                status = int(status) if status not in (None, "") else 0
            except (TypeError, ValueError):
                status = 0
            perspective = data.get("perspective") or data.get("pid") or data.get("perspective_id")
            if perspective is not None and perspective != "":
                try:
                    perspective = int(perspective)
                except (TypeError, ValueError):
                    perspective = None
            i = insight_repo.create_insight(
                content=content,
                type=itype,
                status=status,
                perspective=perspective,
            )
            return resp_ok(_to_dict(i))
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[InsightListView.post] Error: %s", e)
            return resp_exception(e)


class InsightDetailView(APIView):
    """GET, PUT, DELETE insight by id."""

    def get(self, request, insight_id):
        try:
            iid = int(insight_id)
            i = insight_repo.get_insight_by_id(iid)
            if not i:
                return resp_err(code=RET_RESOURCE_NOT_FOUND, message="Insight not found")
            return resp_ok(_to_dict(i))
        except (TypeError, ValueError):
            return resp_err(code=RET_INVALID_PARAM, message="Invalid insight_id")
        except Exception as e:
            logger.exception("[InsightDetailView] Error: %s", e)
            return resp_exception(e)

    def put(self, request, insight_id):
        try:
            iid = int(insight_id)
            data = getattr(request, "data", None) or request.POST or {}
            updates = {}
            if "content" in data:
                updates["content"] = (data["content"] or "").strip()
            if "type" in data:
                try:
                    updates["type"] = int(data["type"])
                except (TypeError, ValueError):
                    pass
            if "status" in data:
                try:
                    updates["status"] = int(data["status"])
                except (TypeError, ValueError):
                    pass
            if "perspective" in data or "pid" in data or "perspective_id" in data:
                v = data.get("perspective") or data.get("pid") or data.get("perspective_id")
                try:
                    updates["perspective"] = int(v) if v not in (None, "") else None
                except (TypeError, ValueError):
                    pass
            if not updates:
                i = insight_repo.get_insight_by_id(iid)
                if not i:
                    return resp_err(code=RET_RESOURCE_NOT_FOUND, message="Insight not found")
                return resp_ok(_to_dict(i))
            ok = insight_repo.update_insight(iid, **updates)
            if not ok:
                return resp_err(code=RET_RESOURCE_NOT_FOUND, message="Insight not found")
            i = insight_repo.get_insight_by_id(iid)
            return resp_ok(_to_dict(i))
        except (TypeError, ValueError) as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[InsightDetailView.put] Error: %s", e)
            return resp_exception(e)

    def delete(self, request, insight_id):
        try:
            iid = int(insight_id)
            ok = insight_repo.delete_insight(iid)
            if not ok:
                return resp_err(code=RET_RESOURCE_NOT_FOUND, message="Insight not found")
            return resp_ok({"deleted": True})
        except (TypeError, ValueError):
            return resp_err(code=RET_INVALID_PARAM, message="Invalid insight_id")
        except Exception as e:
            logger.exception("[InsightDetailView.delete] Error: %s", e)
            return resp_exception(e)


class InsightGenerateView(APIView):
    """POST: generate insights. Body: kid (required, batch_id), perspective, types (list of int)."""

    def post(self, request):
        try:
            data = getattr(request, "data", None) or request.POST or {}
            kid = data.get("kid") or data.get("batch_id")
            if not kid:
                return resp_err(code=RET_INVALID_PARAM, message="kid is required")
            kid = int(kid)
            perspective = data.get("perspective") or data.get("pid") or data.get("perspective_id")
            if perspective is not None and perspective != "":
                try:
                    perspective = int(perspective)
                except (TypeError, ValueError):
                    perspective = None
            types = data.get("types")
            if isinstance(types, list):
                types = [int(t) for t in types]
            elif isinstance(types, str):
                types = [int(t.strip()) for t in types.split(",") if t.strip()] if types else [1]
            else:
                types = [1]  # INSIGHT_PATH_REASONING
            results = generate_insights_and_store(batch_id=kid, perspective=perspective, types=types)
            return resp_ok({"kid": kid, "generated": len(results), "insights": results})
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[InsightGenerateView] Error: %s", e)
            return resp_exception(e)
