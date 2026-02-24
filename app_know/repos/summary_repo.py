"""
MongoDB repository for knowledge summaries (Atlas). Generated.
Upsert/get/list/delete by knowledge_id and app_id.
Logical query: search by summary relevance (text/regex). Generated.
Vector search: search by semantic similarity on summary embedding.
"""
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from pymongo.errors import ConnectionFailure, PyMongoError

from common.consts.query_const import LIMIT_LIST
from common.drivers.mongo_driver import MongoDriver
from common.services.text.text_helper import TextHelper, VEC_DIM
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_summaries"

# Max stored summary length (chars); reject longer to avoid abuse
SUMMARY_STORAGE_MAX_LEN = 50_000

# Max query length for text search (avoid regex DoS and oversized requests)
QUERY_SEARCH_MAX_LEN = 2000

# Document keys
KEY_KID = "kid"
KEY_SUMMARY = "summary"
KEY_SUMMARY_VEC = "summary_vec"
KEY_APP_ID = "app_id"
KEY_CT = "ct"
KEY_UT = "ut"
KEY_ID = "_id"

# Vector dimension for summary embedding (must match TextHelper.VEC_DIM)
SUMMARY_VEC_DIM = VEC_DIM

# Singleton driver instance (lazy initialization)
_mongo_driver: Optional[MongoDriver] = None
_text_helper = None


def _get_mongo_driver() -> MongoDriver:
    """Get the singleton MongoDriver instance for app_know."""
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


def _get_text_helper() -> TextHelper:
    """Get TextHelper for embedding generation."""
    global _text_helper
    if _text_helper is None:
        _text_helper = TextHelper()
    return _text_helper


def _ensure_index(coll) -> None:
    """Ensure unique index on (kid, app_id) for upsert semantics."""
    try:
        coll.create_index(
            [(KEY_KID, 1), (KEY_APP_ID, 1)],
            unique=True,
            name="idx_kid_app_id",
        )
    except PyMongoError as e:
        logger.warning("[summary_repo] Index creation (may already exist): %s", e)


def save_summary(
    knowledge_id: int,
    summary: str,
    app_id: int,
) -> Dict[str, Any]:
    """
    Upsert a summary document by (kid, app_id). knowledge_id is stored as kid.
    Returns the document as stored (with _id, ct, ut).
    Raises ValueError for invalid inputs; PyMongoError/ConnectionFailure on DB errors.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if summary is None:
        raise ValueError("summary must be a string")
    if not isinstance(summary, str):
        raise ValueError("summary must be a string")
    if len(summary) > SUMMARY_STORAGE_MAX_LEN:
        raise ValueError(f"summary must not exceed {SUMMARY_STORAGE_MAX_LEN} characters")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    now_ms = int(time.time() * 1000)
    doc = {
        KEY_KID: knowledge_id,
        KEY_SUMMARY: summary,
        KEY_APP_ID: app_id,
        KEY_CT: now_ms,
        KEY_UT: now_ms,
    }
    try:
        helper = _get_text_helper()
        vec = helper.generate_vector(summary)
        if vec and len(vec) == SUMMARY_VEC_DIM:
            doc[KEY_SUMMARY_VEC] = vec
        else:
            logger.warning("[save_summary] Failed to generate embedding for summary, kid=%s", knowledge_id)
    except Exception as e:
        logger.warning("[save_summary] Failed to generate embedding for kid=%s: %s", knowledge_id, e)
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        _ensure_index(coll)
        filter_q = {KEY_KID: knowledge_id, KEY_APP_ID: app_id}
        existing = coll.find_one(filter_q)
        if existing:
            update = {
                "$set": {
                    KEY_SUMMARY: doc[KEY_SUMMARY],
                    KEY_UT: now_ms,
                }
            }
            if KEY_SUMMARY_VEC in doc:
                update["$set"][KEY_SUMMARY_VEC] = doc[KEY_SUMMARY_VEC]
            coll.update_one(filter_q, update)
            doc[KEY_CT] = existing.get(KEY_CT, now_ms)
            doc[KEY_UT] = now_ms
            doc[KEY_ID] = existing[KEY_ID]
        else:
            coll.insert_one(doc)
        return _doc_to_item(doc)
    except ConnectionFailure:
        raise
    except PyMongoError as e:
        logger.exception("[save_summary] Error: %s", e)
        raise


def get_summary(
    knowledge_id: int,
    app_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get one summary by knowledge_id. If app_id is provided, filter by it.
    Returns None if not found or invalid knowledge_id.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return None
    query = {KEY_KID: knowledge_id}
    if app_id is not None and isinstance(app_id, int) and app_id >= 0:
        query[KEY_APP_ID] = app_id
    logger.info("[get_summary] Query: %s", query)
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        doc = coll.find_one(query)
        logger.info("[get_summary] Found doc: %s", doc is not None)
        if doc is None:
            return None
        return _doc_to_item(doc)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[get_summary] Error: %s", e)
        raise


def list_summaries(
    app_id: Optional[str] = None,
    knowledge_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List summaries with optional filters. Returns (items, total_count).
    Raises ValueError for invalid offset/limit.
    """
    if offset is None:
        raise ValueError("offset is required")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if limit is None:
        raise ValueError("limit is required")
    if not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    query = {}
    if app_id is not None and isinstance(app_id, int) and app_id >= 0:
        query[KEY_APP_ID] = app_id
    if knowledge_id is not None and isinstance(knowledge_id, int) and knowledge_id > 0:
        query[KEY_KID] = knowledge_id
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        total = coll.count_documents(query)
        cursor = coll.find(query).sort(KEY_UT, -1).skip(offset).limit(limit)
        items = [_doc_to_item(d) for d in cursor]
        return items, total
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[list_summaries] Error: %s", e)
        raise


def delete_by_knowledge_id(
    knowledge_id: int,
) -> int:
    """
    Delete all summary documents for the given knowledge_id (sync on knowledge delete).
    Returns the number of documents deleted.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return 0
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.delete_many({KEY_KID: knowledge_id})
        return result.deleted_count
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[delete_by_knowledge_id] Error: %s", e)
        raise


def update_summary(
    knowledge_id: int,
    app_id: int,
    summary: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing summary document by (kid, app_id).
    Returns the updated document or None if not found.
    Raises ValueError for invalid inputs.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if summary is not None:
        if not isinstance(summary, str):
            raise ValueError("summary must be a string")
        if len(summary) > SUMMARY_STORAGE_MAX_LEN:
            raise ValueError(f"summary must not exceed {SUMMARY_STORAGE_MAX_LEN} characters")

    now_ms = int(time.time() * 1000)
    update_fields = {KEY_UT: now_ms}
    if summary is not None:
        update_fields[KEY_SUMMARY] = summary
        try:
            helper = _get_text_helper()
            vec = helper.generate_vector(summary)
            if vec and len(vec) == SUMMARY_VEC_DIM:
                update_fields[KEY_SUMMARY_VEC] = vec
            else:
                logger.warning("[update_summary] Failed to generate embedding for kid=%s", knowledge_id)
        except Exception as e:
            logger.warning("[update_summary] Failed to generate embedding for kid=%s: %s", knowledge_id, e)

    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        filter_q = {KEY_KID: knowledge_id, KEY_APP_ID: app_id}
        result = coll.find_one_and_update(
            filter_q,
            {"$set": update_fields},
            return_document=True,
        )
        if result is None:
            return None
        return _doc_to_item(result)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[update_summary] Error: %s", e)
        raise


def delete_summary(
    knowledge_id: int,
    app_id: int,
) -> bool:
    """
    Delete a summary document by (knowledge_id, app_id).
    Returns True if deleted, False if not found.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")

    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.delete_one({KEY_KID: knowledge_id, KEY_APP_ID: app_id})
        return result.deleted_count > 0
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[delete_summary] Error: %s", e)
        raise


def _regex_escape(text: str) -> str:
    """Escape special regex characters in a string for safe use in $regex."""
    return re.escape(text)


def search_summaries_by_text(
    query: str,
    app_id: Optional[int] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Search summaries by keyword/text relevance (case-insensitive regex on summary field).
    Returns list of dicts with kid, summary, app_id, score (1.0 for match).
    Used by logical query to get candidate knowledge IDs. Raises ValueError for invalid inputs.
    Generated.
    """
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = (query or "").strip()
    if not q:
        raise ValueError("query cannot be empty")
    if len(q) > QUERY_SEARCH_MAX_LEN:
        raise ValueError(f"query must not exceed {QUERY_SEARCH_MAX_LEN} characters")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")
    regex_pattern = _regex_escape(q)
    filter_q = {KEY_SUMMARY: {"$regex": regex_pattern, "$options": "i"}}
    if app_id is not None and isinstance(app_id, int) and app_id >= 0:
        filter_q[KEY_APP_ID] = app_id
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        cursor = coll.find(filter_q).limit(limit)
        items = []
        for doc in cursor:
            item = _doc_to_item(doc)
            item["score"] = 1.0
            items.append(item)
        return items
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[search_summaries_by_text] Error: %s", e)
        raise


def ensure_summary_vector_index() -> bool:
    """
    Create vector search index on knowledge_summaries.summary_vec if not exists.
    Call this once before using search_summaries_by_vector (e.g. via management command).
    Returns True if index created or already exists.
    """
    try:
        driver = _get_mongo_driver()
        driver.create_vector_search_index(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_SUMMARY_VEC,
            dim_num=SUMMARY_VEC_DIM,
            filter_paths=[KEY_APP_ID],
        )
        logger.info(
            "[summary_repo] Vector index ensure attempted for %s.%s",
            COLLECTION_NAME,
            KEY_SUMMARY_VEC,
        )
        return True
    except Exception as e:
        logger.warning("[summary_repo] ensure_summary_vector_index error: %s", e)
        return False


def search_summaries_by_vector_filtered(
    query: str,
    app_id: Optional[int] = None,
    top_k: int = 5,
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Search summaries by semantic similarity, filter by min_score, return top_k.
    Used by knowledge list summary filter.
    Returns list of dicts with kid, summary, app_id, ct, ut, score (ordered by score desc).
    """
    if min_score is None:
        from service_foundation import settings
        min_score = getattr(settings, "KNOW_SIMILARITY_MISMATCH_THRESHOLD", 0.5)
    logger.info("[search_summaries_by_vector_filtered] query=%r, app_id=%s, min_score=%s, top_k=%s", query[:80] if query else "", app_id, min_score, top_k)
    # Fetch more candidates to filter by threshold, then take top_k
    raw = search_summaries_by_vector(query=query, app_id=app_id, limit=50)
    logger.info("[search_summaries_by_vector_filtered] raw count=%s, scores=%s", len(raw), [round(r.get("score", 0), 3) for r in raw[:5]])
    filtered = [r for r in raw if (r.get("score") or 0) >= min_score]
    logger.info("[search_summaries_by_vector_filtered] after min_score filter: count=%s", len(filtered))
    return filtered[:top_k]


def search_summaries_by_vector(
    query: str,
    app_id: Optional[int] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search summaries by semantic similarity using vector search on summary embedding.
    Returns list of dicts with kid, summary, app_id, ct, ut, score.
    """
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = (query or "").strip()
    if not q:
        raise ValueError("query cannot be empty")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be an integer in 1..{LIMIT_LIST}")

    try:
        logger.info("[search_summaries_by_vector] query=%r, app_id=%s, limit=%s", q[:80] if q else "", app_id, limit)
        helper = _get_text_helper()
        query_vec = helper.generate_vector(q)
        if not query_vec or len(query_vec) != SUMMARY_VEC_DIM:
            logger.warning("[search_summaries_by_vector] Invalid embedding for query (vec_len=%s)", len(query_vec) if query_vec else 0)
            return []
        logger.info("[search_summaries_by_vector] embedding ok, vec_dim=%s", len(query_vec))

        driver = _get_mongo_driver()
        proj = {KEY_KID: 1, KEY_SUMMARY: 1, KEY_APP_ID: 1, KEY_CT: 1, KEY_UT: 1, "score": 1}
        filter_query = {KEY_APP_ID: app_id} if app_id is not None and isinstance(app_id, int) and app_id >= 0 else None
        logger.info("[search_summaries_by_vector] filter_query=%s", filter_query)
        results = driver.vector_search(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_SUMMARY_VEC,
            embedded_vec=query_vec,
            cand_num=50,
            limit=limit,
            proj=proj,
            filter_query=filter_query,
        )
        if not results or not isinstance(results, list):
            logger.info("[search_summaries_by_vector] no results: results=%s", type(results).__name__ if results is not None else "None")
            return []
        logger.info("[search_summaries_by_vector] vector_search returned %s docs, top scores=%s", len(results), [round(r.get("score", 0), 3) for r in results[:5]])
        items = []
        for r in results:
            item = _doc_to_item(r)
            item["score"] = r.get("score", 0.0)
            items.append(item)
        return items
    except Exception as e:
        logger.warning("[summary_repo] search_summaries_by_vector error (index may not exist): %s", e)
        raise


def _doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to API-friendly dict (id as string for ObjectId)."""
    out = {
        "kid": doc.get(KEY_KID),
        "summary": doc.get(KEY_SUMMARY, ""),
        "app_id": doc.get(KEY_APP_ID, 0),
        "ct": doc.get(KEY_CT, 0),
        "ut": doc.get(KEY_UT, 0),
    }
    if KEY_ID in doc:
        out["id"] = str(doc[KEY_ID])
    return out
