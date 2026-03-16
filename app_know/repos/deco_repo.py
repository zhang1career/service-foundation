"""
MongoDB repository for sub_deco and obj_deco collections (subject/object decoration vectors).
Used for vector index: build short sentence from graph_subject/graph_object, embed, store in Atlas.
"""
import logging
import time
from typing import Any, Dict, Optional

from pymongo.errors import ConnectionFailure, PyMongoError
from bson import ObjectId

from common.drivers.mongo_driver import MongoDriver
from common.services.text.text_helper import TextHelper, VEC_DIM
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_SUB_DECO = "sub_deco"
COLLECTION_OBJ_DECO = "obj_deco"
# Atlas FTS index names (use existing indexes to avoid hitting instance FTS limit)
INDEX_SUB_DECO = "sub_deco_vec"
INDEX_OBJ_DECO = "obj_deco_vec"

KEY_CONTENT = "content"
KEY_CONTENT_VEC = "content_vec"
KEY_CT = "ct"
KEY_UT = "ut"
KEY_ID = "_id"

_mongo_driver: Optional[MongoDriver] = None
_text_helper: Optional[TextHelper] = None


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


def _upsert_deco(
    coll_name: str,
    content: str,
    existing_id: Optional[str],
    knowledge_id: int,
) -> str:
    """
    Create or update a deco document. If existing_id is set, update that document;
    otherwise insert new. Returns the document _id as string.
    """
    if not content or not isinstance(content, str):
        content = ""
    now_ms = int(time.time() * 1000)
    doc = {
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
            logger.warning("[deco_repo] Failed to generate embedding for knowledge_id=%s coll=%s", knowledge_id, coll_name)
    except Exception as e:
        logger.warning("[deco_repo] Embedding error knowledge_id=%s coll=%s: %s", knowledge_id, coll_name, e)

    driver = _get_mongo_driver()
    coll = driver.create_or_get_collection(coll_name)

    if existing_id and existing_id.strip():
        try:
            oid = ObjectId(existing_id)
        except Exception:
            oid = None
        if oid:
            existing = coll.find_one({KEY_ID: oid})
            if existing:
                update = {"$set": {KEY_CONTENT: content, KEY_UT: now_ms}}
                if KEY_CONTENT_VEC in doc:
                    update["$set"][KEY_CONTENT_VEC] = doc[KEY_CONTENT_VEC]
                coll.update_one({KEY_ID: oid}, update)
                return existing_id

    # Insert new
    coll.insert_one(doc)
    return str(doc[KEY_ID])


def upsert_sub_deco(knowledge_id: int, content: str, existing_id: Optional[str] = None) -> str:
    """Upsert sub_deco document. Returns Mongo _id string."""
    return _upsert_deco(COLLECTION_SUB_DECO, content, existing_id, knowledge_id)


def upsert_obj_deco(knowledge_id: int, content: str, existing_id: Optional[str] = None) -> str:
    """Upsert obj_deco document. Returns Mongo _id string."""
    return _upsert_deco(COLLECTION_OBJ_DECO, content, existing_id, knowledge_id)


def _backfill_content_vec_for_docs(coll_name: str, text: str) -> list:
    """
    Find documents with content==text but missing content_vec, generate embedding and update.
    Returns list of _id (str) that were updated. Used when vector_search returns 0 so those docs get indexed.
    """
    if not text or not isinstance(text, str):
        return []
    driver = _get_mongo_driver()
    coll = driver.create_or_get_collection(coll_name)
    cursor = coll.find({KEY_CONTENT: text.strip()})
    updated_ids = []
    try:
        helper = _get_text_helper()
        now_ms = int(time.time() * 1000)
        for doc in cursor:
            oid = doc.get(KEY_ID)
            if oid is None:
                continue
            if doc.get(KEY_CONTENT_VEC) and len(doc.get(KEY_CONTENT_VEC)) == VEC_DIM:
                continue
            try:
                vec = helper.generate_vector(text)
                if vec and len(vec) == VEC_DIM:
                    coll.update_one(
                        {KEY_ID: oid},
                        {"$set": {KEY_CONTENT_VEC: vec, KEY_UT: now_ms}},
                    )
                    updated_ids.append(str(oid))
            except Exception as e:
                logger.warning("[deco_repo] backfill embed error for _id=%s: %s", oid, e)
    except Exception as e:
        logger.warning("[deco_repo] backfill find error: %s", e)
    return updated_ids


def vector_search_deco(coll_name: str, text: str, limit: int = 5) -> list:
    """
    Run vector similarity search on sub_deco or obj_deco.
    Returns list of dicts with at least "_id" (str). Uses content_vec index.
    If first search returns 0 results, backfills content_vec for docs that have content but no
    content_vec (so they get into the index), then retries vector search once.
    """
    if not text or not isinstance(text, str):
        return []
    try:
        helper = _get_text_helper()
        vec = helper.generate_vector(text)
        if not vec or len(vec) != VEC_DIM:
            logger.warning("[deco_repo] vector_search_deco: embedding failed or wrong dim")
            return []
    except Exception as e:
        logger.warning("[deco_repo] vector_search_deco embed error: %s", e)
        return []
    driver = _get_mongo_driver()
    index_name = INDEX_SUB_DECO if coll_name == COLLECTION_SUB_DECO else INDEX_OBJ_DECO
    results = driver.vector_search(
        coll_name=coll_name,
        attr_name=KEY_CONTENT_VEC,
        embedded_vec=vec,
        limit=limit,
        proj={KEY_ID: 1},
        index_name=index_name,
    )
    out = []
    for doc in results:
        oid = doc.get(KEY_ID)
        if oid is not None:
            out.append({KEY_ID: str(oid)})
    if not out:
        backfilled_ids = _backfill_content_vec_for_docs(coll_name, text)
        if backfilled_ids:
            logger.info("[deco_repo] backfilled content_vec for %d doc(s), retrying vector_search", len(backfilled_ids))
            results = driver.vector_search(
                coll_name=coll_name,
                attr_name=KEY_CONTENT_VEC,
                embedded_vec=vec,
                limit=limit,
                proj={KEY_ID: 1},
                index_name=index_name,
            )
            for doc in results:
                oid = doc.get(KEY_ID)
                if oid is not None:
                    out.append({KEY_ID: str(oid)})
            if not out:
                for oid in backfilled_ids:
                    out.append({KEY_ID: oid})
        else:
            logger.info(
                "[deco_repo] vector_search returned 0 results (coll=%s). "
                "Ensure vector index exists (run: python manage.py ensure_know_vector_index) "
                "and documents have content_vec field.",
                coll_name,
            )
    return out


def ensure_deco_vector_index() -> bool:
    """
    Ensure deco vector indexes exist. Skips creation to avoid Atlas FTS index limit;
    queries use existing indexes sub_deco_vec and obj_deco_vec.
    Returns True (caller can assume indexes are available).
    """
    logger.info(
        "[deco_repo] deco vector search uses existing Atlas indexes: %s, %s (skip create to avoid FTS limit)",
        INDEX_SUB_DECO,
        INDEX_OBJ_DECO,
    )
    return True
