"""
REST API view for extracting relations from knowledge content.
Uses TextAI to extract predicate logic and stores in Atlas + Neo4j.
"""
import json
import logging

from rest_framework import status as http_status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.services.knowledge_service import KnowledgeService
from app_know.repos import component_repo
from app_know.services.relation_extractor import (
    ExtractedRelation,
    extract_relations_from_content,
    get_relation_graph_by_knowledge_id,
    store_relation_in_graph,
    update_graph_node_name,
    update_graph_relationship_type,
)
from app_know.services.summary_service import SummaryService, _validate_app_id
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
    RET_AI_ERROR,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _parse_entity_id(entity_id) -> int:
    """Parse and validate entity_id from URL. Raises ValueError if invalid."""
    if entity_id is None or entity_id == "":
        raise ValueError("entity_id is required")
    if isinstance(entity_id, float) and not entity_id.is_integer():
        raise ValueError("entity_id must be an integer")
    try:
        eid = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")
    if eid <= 0:
        raise ValueError("entity_id must be a positive integer")
    return eid


def _error_code_for_validation(msg: str) -> int:
    """Map ValueError message to response error code."""
    m = msg.lower()
    if "not found" in m:
        return RET_RESOURCE_NOT_FOUND
    if "required" in m or "cannot be empty" in m or "missing" in m:
        return RET_MISSING_PARAM
    return RET_INVALID_PARAM


class RelationExtractView(APIView):
    """POST: extract relations from knowledge content and store in graph databases."""

    def post(self, request, entity_id, *args, **kwargs):
        """
        Extract relations from knowledge content.
        
        Body:
            app_id: Application ID (required)
        
        Returns:
            List of extracted relations with:
            - subject: Subject text
            - predicate: Predicate text
            - object: Object text
            - subject_node_id: Atlas _id of subject node
            - object_node_id: Atlas _id of object node
            - neo4j_relationship_id: Neo4j relationship ID
        """
        try:
            entity_id = _parse_entity_id(entity_id)
            
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}
            
            raw_app_id = data.get("app_id")
            app_id = _validate_app_id(raw_app_id)  # default 0
            
            service = KnowledgeService()
            knowledge = service.get_knowledge(entity_id)

            summary_service = SummaryService()
            summary_result = summary_service.get_summary(
                knowledge_id=entity_id,
                app_id=app_id,
            )
            if not summary_result or not summary_result.get("summary", "").strip():
                return resp_err(
                    "Knowledge summary is empty, please generate summary first",
                    code=RET_INVALID_PARAM,
                    status=http_status.HTTP_200_OK,
                )
            content = summary_result["summary"].strip()

            relations = extract_relations_from_content(
                content=content,
                app_id=app_id,
                knowledge_id=entity_id,
            )

            results = []
            for r in relations:
                subject_candidates = component_repo.find_similar_nodes(
                    r.subject, app_id, limit=5
                )
                object_candidates = component_repo.find_similar_nodes(
                    r.obj, app_id, limit=5
                )
                subject_names = {c["name"] for c in subject_candidates}
                object_names = {c["name"] for c in object_candidates}
                if r.subject and r.subject not in subject_names:
                    subject_candidates = [{"id": "", "name": r.subject, "score": 0.0}] + subject_candidates
                if r.obj and r.obj not in object_names:
                    object_candidates = [{"id": "", "name": r.obj, "score": 0.0}] + object_candidates
                results.append({
                    "subject": r.subject,
                    "predicate": r.predicate,
                    "object": r.obj,
                    "subject_candidates": [
                        {"id": c.get("id", ""), "name": c.get("name", ""), "score": float(c.get("score", 0.0))}
                        for c in subject_candidates
                    ],
                    "object_candidates": [
                        {"id": c.get("id", ""), "name": c.get("name", ""), "score": float(c.get("score", 0.0))}
                        for c in object_candidates
                    ],
                })

            return resp_ok({
                "knowledge_id": entity_id,
                "relations": results,
                "count": len(results),
            })
        except ValueError as e:
            logger.warning("[RelationExtractView.post] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except RuntimeError as e:
            logger.warning("[RelationExtractView.post] Runtime error: %s", e)
            return resp_err(
                str(e),
                code=RET_AI_ERROR,
                status=http_status.HTTP_200_OK,
            )
        except ParseError as e:
            logger.warning("[RelationExtractView.post] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationExtractView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class RelationSaveView(APIView):
    """POST: save a relation (subject, predicate, object) to Neo4j."""

    def post(self, request, entity_id, *args, **kwargs):
        """
        Save relation to graph databases.

        Body:
            app_id: Application ID (required)
            subject: Subject text (required)
            predicate: Predicate text (required)
            object: Object text (required)
        """
        try:
            entity_id = _parse_entity_id(entity_id)

            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}

            raw_app_id = data.get("app_id")
            app_id = _validate_app_id(raw_app_id)

            subject = (data.get("subject") or "").strip()
            predicate = (data.get("predicate") or "").strip()
            obj = (data.get("object") or "").strip()

            if not subject:
                return resp_err("subject is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            if not predicate:
                return resp_err("predicate is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            if not obj:
                return resp_err("object is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)

            relation = ExtractedRelation(subject=subject, predicate=predicate, obj=obj)
            stored = store_relation_in_graph(relation, app_id=app_id, knowledge_id=entity_id)

            return resp_ok({
                "knowledge_id": entity_id,
                "subject": stored.subject,
                "predicate": stored.predicate,
                "object": stored.obj,
                "subject_node_id": stored.subject_node_id,
                "object_node_id": stored.obj_node_id,
                "neo4j_relationship_id": stored.neo4j_relationship_id,
            })
        except ValueError as e:
            logger.warning("[RelationSaveView.post] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("[RelationSaveView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class RelationGraphView(APIView):
    """GET: fetch Neo4j relation graph for a knowledge entity (kid -> table y -> cid -> Neo4j)."""

    def get(self, request, entity_id, *args, **kwargs):
        """
        Get relation graph for knowledge entity.
        Query param: app_id (optional, default 0)
        """
        try:
            entity_id = _parse_entity_id(entity_id)
            raw_app_id = request.query_params.get("app_id", 0)
            app_id = _validate_app_id(raw_app_id)

            graph_data = get_relation_graph_by_knowledge_id(
                knowledge_id=entity_id,
                app_id=app_id,
            )
            return resp_ok(graph_data)
        except ValueError as e:
            logger.warning("[RelationGraphView.get] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("[RelationGraphView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class RelationGraphNodeUpdateView(APIView):
    """PATCH/POST: update graph node name by cid."""

    def patch(self, request, entity_id, *args, **kwargs):
        return self._update_node(request, entity_id)

    def post(self, request, entity_id, *args, **kwargs):
        return self._update_node(request, entity_id)

    def _update_node(self, request, entity_id):
        """Body: cid (required), name (required), app_id (optional, default 0)."""
        try:
            _parse_entity_id(entity_id)
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}
            cid = (data.get("cid") or "").strip()
            name = (data.get("name") or "").strip()
            app_id = _validate_app_id(data.get("app_id", 0))
            if not cid:
                return resp_err("cid is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            ok = update_graph_node_name(cid=cid, name=name or cid, app_id=app_id)
            if not ok:
                return resp_err("Node not found or update failed", code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_ok({"cid": cid, "name": name or cid})
        except ValueError as e:
            return resp_err(str(e), code=_error_code_for_validation(str(e)), status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationGraphNodeUpdateView.patch] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class RelationGraphEdgeUpdateView(APIView):
    """PATCH/POST: update graph relationship type (delete old, create new)."""

    def patch(self, request, entity_id, *args, **kwargs):
        return self._update_edge(request, entity_id)

    def post(self, request, entity_id, *args, **kwargs):
        return self._update_edge(request, entity_id)

    def _update_edge(self, request, entity_id):
        """Body: from_cid, to_cid, old_type, new_type, app_id (optional)."""
        try:
            _parse_entity_id(entity_id)
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}
            from_cid = (data.get("from_cid") or data.get("from") or "").strip()
            to_cid = (data.get("to_cid") or data.get("to") or "").strip()
            old_type = (data.get("old_type") or "").strip()
            new_type = (data.get("new_type") or "").strip()
            app_id = _validate_app_id(data.get("app_id", 0))
            if not from_cid or not to_cid:
                return resp_err("from_cid and to_cid are required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            if not old_type or not new_type:
                return resp_err("old_type and new_type are required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            ok = update_graph_relationship_type(
                from_cid=from_cid, to_cid=to_cid, old_type=old_type, new_type=new_type, app_id=app_id
            )
            if not ok:
                return resp_err("Relationship not found or update failed", code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_ok({"from": from_cid, "to": to_cid, "type": new_type})
        except ValueError as e:
            return resp_err(str(e), code=_error_code_for_validation(str(e)), status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationGraphEdgeUpdateView.patch] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
