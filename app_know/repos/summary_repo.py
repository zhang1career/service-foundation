"""
MongoDB repository for knowledge summaries (Atlas). Generated.
Upsert/get/list/delete by knowledge_id and app_id.
Logical query: search by summary relevance (text/regex). Generated.
"""
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from pymongo.errors import ConnectionFailure, PyMongoError

from common.consts.query_const import LIMIT_LIST
from common.drivers.mongo_driver import MongoDriver
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_summaries"

# Max stored summary length (chars); reject longer to avoid abuse
SUMMARY_STORAGE_MAX_LEN = 50_000

# Max query length for text search (avoid regex DoS and oversized requests)
QUERY_SEARCH_MAX_LEN = 2000

# Document keys
KEY_KNOWLEDGE_ID = "knowledge_id"
KEY_SUMMARY = "summary"
KEY_APP_ID = "app_id"
KEY_SOURCE = "source"
KEY_CT = "ct"
KEY_UT = "ut"
KEY_ID = "_id"

# Singleton driver instance (lazy initialization)
_mongo_driver: Optional[MongoDriver] = None


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


def _ensure_index(coll) -> None:
    """Ensure unique index on (knowledge_id, app_id) for upsert semantics."""
    try:
        coll.create_index(
            [(KEY_KNOWLEDGE_ID, 1), (KEY_APP_ID, 1)],
            unique=True,
            name="idx_knowledge_id_app_id",
        )
    except PyMongoError as e:
        logger.warning("[summary_repo] Index creation (may already exist): %s", e)


def save_summary(
    knowledge_id: int,
    summary: str,
    app_id: str,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Upsert a summary document by (knowledge_id, app_id).
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
    if source is not None and not isinstance(source, str):
        raise ValueError("source must be a string or None")
    app_id = (app_id or "").strip()
    if not app_id:
        raise ValueError("app_id is required and cannot be empty")
    now_ms = int(time.time() * 1000)
    doc = {
        KEY_KNOWLEDGE_ID: knowledge_id,
        KEY_SUMMARY: summary,
        KEY_APP_ID: app_id,
        KEY_SOURCE: (source or "title_description").strip() or "title_description",
        KEY_CT: now_ms,
        KEY_UT: now_ms,
    }
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        _ensure_index(coll)
        filter_q = {KEY_KNOWLEDGE_ID: knowledge_id, KEY_APP_ID: app_id}
        existing = coll.find_one(filter_q)
        if existing:
            update = {
                "$set": {
                    KEY_SUMMARY: doc[KEY_SUMMARY],
                    KEY_SOURCE: doc[KEY_SOURCE],
                    KEY_UT: now_ms,
                }
            }
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
    app_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get one summary by knowledge_id. If app_id is provided, filter by it.
    Returns None if not found or invalid knowledge_id.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        return None
    query = {KEY_KNOWLEDGE_ID: knowledge_id}
    if app_id is not None and str(app_id).strip():
        query[KEY_APP_ID] = str(app_id).strip()
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        doc = coll.find_one(query)
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
    if app_id is not None and str(app_id).strip():
        query[KEY_APP_ID] = str(app_id).strip()
    if knowledge_id is not None and isinstance(knowledge_id, int) and knowledge_id > 0:
        query[KEY_KNOWLEDGE_ID] = knowledge_id
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
        result = coll.delete_many({KEY_KNOWLEDGE_ID: knowledge_id})
        return result.deleted_count
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[delete_by_knowledge_id] Error: %s", e)
        raise


def update_summary(
    knowledge_id: int,
    app_id: str,
    summary: Optional[str] = None,
    source: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing summary document by (knowledge_id, app_id).
    Returns the updated document or None if not found.
    Raises ValueError for invalid inputs.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    app_id = (app_id or "").strip()
    if not app_id:
        raise ValueError("app_id is required and cannot be empty")
    if summary is not None:
        if not isinstance(summary, str):
            raise ValueError("summary must be a string")
        if len(summary) > SUMMARY_STORAGE_MAX_LEN:
            raise ValueError(f"summary must not exceed {SUMMARY_STORAGE_MAX_LEN} characters")
    if source is not None and not isinstance(source, str):
        raise ValueError("source must be a string or None")

    now_ms = int(time.time() * 1000)
    update_fields = {KEY_UT: now_ms}
    if summary is not None:
        update_fields[KEY_SUMMARY] = summary
    if source is not None:
        update_fields[KEY_SOURCE] = source.strip() or "title_description"

    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        filter_q = {KEY_KNOWLEDGE_ID: knowledge_id, KEY_APP_ID: app_id}
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
    app_id: str,
) -> bool:
    """
    Delete a summary document by (knowledge_id, app_id).
    Returns True if deleted, False if not found.
    """
    if knowledge_id is None or not isinstance(knowledge_id, int) or knowledge_id <= 0:
        raise ValueError("knowledge_id must be a positive integer")
    app_id = (app_id or "").strip()
    if not app_id:
        raise ValueError("app_id is required and cannot be empty")

    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.delete_one({KEY_KNOWLEDGE_ID: knowledge_id, KEY_APP_ID: app_id})
        return result.deleted_count > 0
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[delete_summary] Error: %s", e)
        raise


def _regex_escape(text: str) -> str:
    """Escape special regex characters in a string for safe use in $regex."""
    return re.escape(text)


def search_summaries_by_text(
    query: str,
    app_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Search summaries by keyword/text relevance (case-insensitive regex on summary field).
    Returns list of dicts with knowledge_id, summary, app_id, score (1.0 for match).
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
    if app_id is not None and str(app_id).strip():
        filter_q[KEY_APP_ID] = str(app_id).strip()
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


def _doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to API-friendly dict (id as string for ObjectId)."""
    out = {
        "knowledge_id": doc.get(KEY_KNOWLEDGE_ID),
        "summary": doc.get(KEY_SUMMARY, ""),
        "app_id": doc.get(KEY_APP_ID, ""),
        "source": doc.get(KEY_SOURCE, "title_description"),
        "ct": doc.get(KEY_CT, 0),
        "ut": doc.get(KEY_UT, 0),
    }
    if KEY_ID in doc:
        out["id"] = str(doc[KEY_ID])
    return out
