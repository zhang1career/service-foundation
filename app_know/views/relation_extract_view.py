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
from app_know.services.relation_extractor import (
    ExtractedRelation,
    extract_relations_from_content,
    resolve_relations_via_atlas,
    store_relation_in_graph,
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
            relations = resolve_relations_via_atlas(relations, app_id=app_id)

            results = [
                {"subject": r.subject, "predicate": r.predicate, "object": r.obj}
                for r in relations
            ]

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
