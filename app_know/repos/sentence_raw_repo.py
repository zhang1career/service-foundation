"""
MongoDB repository for sentence_raw (sentence vectors in Atlas).
Stores sentence embedding for vector similarity search.
Document links to MySQL sentence via sentence_id.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from pymongo.errors import ConnectionFailure, PyMongoError

from common.drivers.mongo_driver import MongoDriver
from app_know.services.text_helper import TextHelper, VEC_DIM
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "sentence_raw"

KEY_SENTENCE_ID = "sentence_id"
KEY_CONTENT = "content"
KEY_CONTENT_VEC = "content_vec"
KEY_CT = "ct"
KEY_UT = "ut"
KEY_ID = "_id"

_mongo_driver: Optional[MongoDriver] = None
_text_helper = None


def _get_mongo_driver() -> MongoDriver:
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
    global _text_helper
    if _text_helper is None:
        _text_helper = TextHelper()
    return _text_helper


def _ensure_index(coll):
    try:
        coll.create_index(
            [(KEY_SENTENCE_ID, 1)],
            unique=True,
            name="idx_sentence_id",
        )
    except PyMongoError as e:
        logger.warning("[sentence_raw_repo] Index creation (may already exist): %s", e)


def save_sentence_raw(sentence_id: int, content: str) -> Dict[str, Any]:
    """
    Upsert sentence_raw by sentence_id.
    Generates embedding from content and stores in Atlas.
    Returns document as dict with id, sentence_id, etc.
    """
    if sentence_id is None or not isinstance(sentence_id, int) or sentence_id <= 0:
        raise ValueError("sentence_id must be a positive integer")
    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ValueError("content must be a string")

    now_ms = int(time.time() * 1000)
    doc = {
        KEY_SENTENCE_ID: sentence_id,
        KEY_CONTENT: content,
        KEY_CT: now_ms,
        KEY_UT: now_ms,
    }
    try:
        helper = _get_text_helper()
        vec = helper.generate_vector(content)
        if vec and len(vec) == VEC_DIM:
            doc[KEY_CONTENT_VEC] = vec
        else:
            logger.warning("[save_sentence_raw] Failed to generate embedding for sentence_id=%s", sentence_id)
    except Exception as e:
        logger.warning("[save_sentence_raw] Embedding error for sentence_id=%s: %s", sentence_id, e)

    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        _ensure_index(coll)
        filter_q = {KEY_SENTENCE_ID: sentence_id}
        existing = coll.find_one(filter_q)
        if existing:
            update = {"$set": {KEY_CONTENT: content, KEY_UT: now_ms}}
            if KEY_CONTENT_VEC in doc:
                update["$set"][KEY_CONTENT_VEC] = doc[KEY_CONTENT_VEC]
            coll.update_one(filter_q, update)
            doc[KEY_CT] = existing.get(KEY_CT, now_ms)
            doc[KEY_ID] = existing[KEY_ID]
        else:
            coll.insert_one(doc)
        return _doc_to_item(doc)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[save_sentence_raw] Error: %s", e)
        raise


def search_sentences_by_vector(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search sentences by semantic similarity. Returns list with sentence_id, content, score."""
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")
    q = query.strip()
    if not q:
        raise ValueError("query cannot be empty")

    try:
        helper = _get_text_helper()
        query_vec = helper.generate_vector(q)
        if not query_vec or len(query_vec) != VEC_DIM:
            return []

        driver = _get_mongo_driver()
        proj = {KEY_SENTENCE_ID: 1, KEY_CONTENT: 1, "score": 1}
        results = driver.vector_search(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_CONTENT_VEC,
            embedded_vec=query_vec,
            cand_num=50,
            limit=limit,
            proj=proj,
            filter_query=None,
        )
        if not results or not isinstance(results, list):
            return []
        return [_doc_to_item(r) for r in results]
    except Exception as e:
        logger.warning("[search_sentences_by_vector] error: %s", e)
        raise


def ensure_sentence_raw_vector_index() -> bool:
    """Create vector search index on sentence_raw.content_vec if not exists."""
    try:
        driver = _get_mongo_driver()
        driver.create_vector_search_index(
            coll_name=COLLECTION_NAME,
            attr_name=KEY_CONTENT_VEC,
            dim_num=VEC_DIM,
            filter_paths=None,
        )
        logger.info("[sentence_raw_repo] Vector index ensure attempted for %s.%s", COLLECTION_NAME, KEY_CONTENT_VEC)
        return True
    except Exception as e:
        logger.warning("[sentence_raw_repo] ensure_sentence_raw_vector_index error: %s", e)
        return False


def delete_by_sentence_ids(sentence_ids: List[int]) -> int:
    """Delete sentence_raw docs by sentence_ids. Returns count deleted."""
    if not sentence_ids:
        return 0
    valid_ids = [i for i in sentence_ids if isinstance(i, int) and i > 0]
    if not valid_ids:
        return 0
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        result = coll.delete_many({KEY_SENTENCE_ID: {"$in": valid_ids}})
        return result.deleted_count
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[sentence_raw_repo] delete_by_sentence_ids error: %s", e)
        raise


def _doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "sentence_id": doc.get(KEY_SENTENCE_ID),
        "content": doc.get(KEY_CONTENT, ""),
        "score": doc.get("score", 0.0),
    }
    if KEY_ID in doc:
        out["id"] = str(doc[KEY_ID])
    return out
