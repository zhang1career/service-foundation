"""
MongoDB repository for graph nodes (Atlas).
Stores extracted entities (subjects/objects) from knowledge relations.
Supports duplicate checking and upsert by node name.
Supports vector similarity search on name.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

from common.drivers.mongo_driver import MongoDriver
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_components"

KEY_ID = "_id"
KEY_NAME = "name"
KEY_APP_ID = "app_id"
KEY_NODE_TYPE = "node_type"
KEY_CT = "ct"
KEY_UT = "ut"
KEY_NAME_VEC = "name_vec"

# Vector dimension for name embedding (all-MiniLM-L6-v2)
NAME_VEC_DIM = 384

_mongo_driver: Optional[MongoDriver] = None
_text_helper = None


def _get_mongo_driver() -> MongoDriver:
    """Get the singleton MongoDriver instance."""
    global _mongo_driver
    if _mongo_driver is None:
        _mongo_driver = MongoDriver(
            host=settings.MONGO_ATLAS_HOST,
            username=settings.MONGO_ATLAS_USER,
            password=settings.MONGO_ATLAS_PASS,
            cluster=settings.MONGO_ATLAS_CLUSTER,
            db_name=settings.MONGO_ATLAS_DB,
        )
    return _mongo_driver


def _get_text_helper():
    """Get TextHelper for embedding generation."""
    global _text_helper
    if _text_helper is None:
        from common.services.text.text_helper import TextHelper
        _text_helper = TextHelper()
    return _text_helper


def _ensure_index(coll) -> None:
    """Ensure unique index on (name, app_id) for upsert semantics."""
    try:
        coll.create_index(
            [(KEY_NAME, 1), (KEY_APP_ID, 1)],
            unique=True,
            name="idx_name_app_id",
        )
    except PyMongoError as e:
        logger.warning("[component_repo] Index creation (may already exist): %s", e)


def _vector_search_node(
    name: str,
    app_id: int,
    limit: int = 1,
    include_score: bool = False,
) -> tuple[Optional[list], Optional[list[float]]]:
    """
    Vector search for nodes by name similarity. Returns (results, scores) or (None, None) on error.
    """
    if not name or not isinstance(name, str):
        return None, None
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        return None, None
    name = name.strip()
    if not name:
        return None, None

    try:
        helper = _get_text_helper()
        query_vec = helper.generate_vector(name)
        if not query_vec or len(query_vec) != NAME_VEC_DIM:
            return None, None

        driver = _get_mongo_driver()
        proj = {"name": 1, "app_id": 1, "node_type": 1, "_id": 1, "ct": 1, "ut": 1}
        if include_score:
            proj["score"] = 1
        results = driver.vector_search(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_NAME_VEC,
            embedded_vec=query_vec,
            cand_num=50,
            limit=min(limit * 5, 25),
            proj=proj,
            filter_query={KEY_APP_ID: app_id},
        )
        if not results or not isinstance(results, list):
            return None, None
        scores = [r.get("score", 0.0) for r in results] if include_score else None
        return results, scores
    except Exception as e:
        logger.warning("[component_repo] vector search error (index may not exist): %s", e)
        return None, None


def find_similar_node(name: str, app_id: int, limit: int = 1) -> Optional[Dict[str, Any]]:
    """
    Find a similar graph node by vector search on name.
    Returns the best match or None if no similar node found.
    Requires knowledge_components to have name_vec field and vector index.
    """
    results, _ = _vector_search_node(name, app_id, limit=limit, include_score=False)
    if not results:
        return None
    return _doc_to_item(results[0])


def find_similar_nodes(name: str, app_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find top N similar graph nodes by vector search on name.
    Returns list of nodes with id, name, score (0-1 similarity), ordered by similarity (best first).
    Used for subject/object candidate dropdowns in relation extraction UI.
    """
    results, scores = _vector_search_node(name, app_id, limit=limit, include_score=True)
    if not results:
        return []
    out = []
    for i, doc in enumerate(results[:limit]):
        item = _doc_to_item(doc)
        item["score"] = float(scores[i]) if scores and i < len(scores) else 0.0
        out.append(item)
    return out


def find_node_by_name(name: str, app_id: int) -> Optional[Dict[str, Any]]:
    """
    Find a graph node by name similarity (vector search on name).
    Returns the most similar node or None if not found.
    """
    return find_similar_node(name, app_id, limit=1)


def find_node_by_id(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a graph node by _id.
    Returns None if not found.
    """
    if not node_id or not isinstance(node_id, str):
        return None
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        doc = coll.find_one({KEY_ID: ObjectId(node_id)})
        if doc is None:
            return None
        return _doc_to_item(doc)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[component_repo] find_node_by_id error: %s", e)
        raise


def get_or_create_node(
    name: str,
    app_id: int,
    node_type: str = "entity",
) -> Dict[str, Any]:
    """
    Get existing node or create new one.
    Returns the node document with _id.

    Args:
        name: Node name (subject or object text)
        app_id: Application ID (integer)
        node_type: Type of node (default: "entity")

    Returns:
        Dict with id, name, app_id, node_type, ct, ut, is_new (bool)
    """
    if not name or not isinstance(name, str):
        raise ValueError("name is required and must be a string")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")

    name = name.strip()
    if not name:
        raise ValueError("name cannot be empty")
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        _ensure_index(coll)

        results, scores = _vector_search_node(name, app_id, limit=1, include_score=True)
        if results and scores and scores[0] >= settings.KNOW_SIMILARITY_REUSE_THRESHOLD:
            result = _doc_to_item(results[0])
            result["is_new"] = False
            return result

        # Exact match before insert: avoid DuplicateKeyError when (name, app_id) already exists
        # (e.g. vector search missed it due to threshold or embedding variance)
        existing = coll.find_one({KEY_NAME: name, KEY_APP_ID: app_id})
        if existing:
            result = _doc_to_item(existing)
            result["is_new"] = False
            return result

        now_ms = int(time.time() * 1000)
        doc = {
            KEY_NAME: name,
            KEY_APP_ID: app_id,
            KEY_NODE_TYPE: node_type,
            KEY_CT: now_ms,
            KEY_UT: now_ms,
        }
        try:
            helper = _get_text_helper()
            vec = helper.generate_vector(name)
            if vec and len(vec) == NAME_VEC_DIM:
                doc[KEY_NAME_VEC] = vec
        except Exception as e:
            logger.warning("[component_repo] Failed to generate embedding for name '%s': %s", name[:50], e)
        try:
            insert_result = coll.insert_one(doc)
            doc[KEY_ID] = insert_result.inserted_id
            result = _doc_to_item(doc)
            result["is_new"] = True
            return result
        except DuplicateKeyError:
            # Race: another request inserted between our find and insert
            existing = coll.find_one({KEY_NAME: name, KEY_APP_ID: app_id})
            if existing:
                result = _doc_to_item(existing)
                result["is_new"] = False
                return result
            raise
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[component_repo] get_or_create_node error: %s", e)
        raise


def update_node(
    node_id: str,
    name: Optional[str] = None,
    node_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update a graph node by _id.
    Returns updated node or None if not found.
    When name is updated, regenerates name_vec for vector similarity search.
    """
    if not node_id or not isinstance(node_id, str):
        raise ValueError("node_id is required and must be a string")
    
    update_fields = {KEY_UT: int(time.time() * 1000)}
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("name cannot be empty")
        update_fields[KEY_NAME] = name
        try:
            helper = _get_text_helper()
            vec = helper.generate_vector(name)
            if vec and len(vec) == NAME_VEC_DIM:
                update_fields[KEY_NAME_VEC] = vec
            else:
                logger.warning("[component_repo] Failed to generate embedding for name in update_node: %s", name[:50])
        except Exception as e:
            logger.warning("[component_repo] Failed to generate embedding for name in update_node: %s", e)
    if node_type is not None:
        update_fields[KEY_NODE_TYPE] = node_type
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.find_one_and_update(
            {KEY_ID: ObjectId(node_id)},
            {"$set": update_fields},
            return_document=True,
        )
        if result is None:
            return None
        return _doc_to_item(result)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[component_repo] update_node error: %s", e)
        raise


def delete_node(node_id: str) -> bool:
    """
    Delete a graph node by _id.
    Returns True if deleted, False if not found.
    """
    if not node_id or not isinstance(node_id, str):
        return False
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.delete_one({KEY_ID: ObjectId(node_id)})
        return result.deleted_count > 0
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[component_repo] delete_node error: %s", e)
        raise


def ensure_vector_index() -> bool:
    """
    Create vector search index on knowledge_components.name_vec if not exists.
    Call this once before using find_similar_node (e.g. via management command).
    Returns True if index created or already exists.
    """
    try:
        driver = _get_mongo_driver()
        driver.create_vector_search_index(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_NAME_VEC,
            dim_num=NAME_VEC_DIM,
            filter_paths=[KEY_APP_ID],
        )
        logger.info("[component_repo] Vector index ensure attempted for %s.%s", COLLECTION_NAME, KEY_NAME_VEC)
        return True
    except Exception as e:
        logger.warning("[component_repo] ensure_vector_index error: %s", e)
        return False


def _doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to API-friendly dict."""
    out = {
        "name": doc.get(KEY_NAME, ""),
        "app_id": doc.get(KEY_APP_ID, 0),
        "node_type": doc.get(KEY_NODE_TYPE, "entity"),
        "ct": doc.get(KEY_CT, 0),
        "ut": doc.get(KEY_UT, 0),
    }
    if KEY_ID in doc:
        out["id"] = str(doc[KEY_ID])
    return out
