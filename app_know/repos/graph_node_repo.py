"""
MongoDB repository for graph nodes (Atlas).
Stores extracted entities (subjects/objects) from knowledge relations.
Supports duplicate checking and upsert by node name.
"""
import logging
import time
from typing import Any, Dict, Optional

from bson import ObjectId
from pymongo.errors import ConnectionFailure, PyMongoError

from common.drivers.mongo_driver import MongoDriver
from service_foundation import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "graph_node"

KEY_ID = "_id"
KEY_NAME = "name"
KEY_APP_ID = "app_id"
KEY_NODE_TYPE = "node_type"
KEY_CT = "ct"
KEY_UT = "ut"

_mongo_driver: Optional[MongoDriver] = None


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


def _ensure_index(coll) -> None:
    """Ensure unique index on (name, app_id) for upsert semantics."""
    try:
        coll.create_index(
            [(KEY_NAME, 1), (KEY_APP_ID, 1)],
            unique=True,
            name="idx_name_app_id",
        )
    except PyMongoError as e:
        logger.warning("[graph_node_repo] Index creation (may already exist): %s", e)


def find_node_by_name(name: str, app_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a graph node by name and app_id.
    Returns None if not found.
    """
    if not name or not isinstance(name, str):
        return None
    if not app_id or not isinstance(app_id, str):
        return None
    
    name = name.strip()
    app_id = app_id.strip()
    if not name or not app_id:
        return None
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        doc = coll.find_one({KEY_NAME: name, KEY_APP_ID: app_id})
        if doc is None:
            return None
        return _doc_to_item(doc)
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[graph_node_repo] find_node_by_name error: %s", e)
        raise


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
        logger.exception("[graph_node_repo] find_node_by_id error: %s", e)
        raise


def get_or_create_node(
    name: str,
    app_id: str,
    node_type: str = "entity",
) -> Dict[str, Any]:
    """
    Get existing node or create new one.
    Returns the node document with _id.
    
    Args:
        name: Node name (subject or object text)
        app_id: Application ID
        node_type: Type of node (default: "entity")
    
    Returns:
        Dict with id, name, app_id, node_type, ct, ut, is_new (bool)
    """
    if not name or not isinstance(name, str):
        raise ValueError("name is required and must be a string")
    if not app_id or not isinstance(app_id, str):
        raise ValueError("app_id is required and must be a string")
    
    name = name.strip()
    app_id = app_id.strip()
    if not name:
        raise ValueError("name cannot be empty")
    if not app_id:
        raise ValueError("app_id cannot be empty")
    
    try:
        driver = _get_mongo_driver()
        coll = driver.create_or_get_collection(COLLECTION_NAME)
        _ensure_index(coll)
        
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
        insert_result = coll.insert_one(doc)
        doc[KEY_ID] = insert_result.inserted_id
        
        result = _doc_to_item(doc)
        result["is_new"] = True
        return result
    except (ConnectionFailure, PyMongoError) as e:
        logger.exception("[graph_node_repo] get_or_create_node error: %s", e)
        raise


def update_node(
    node_id: str,
    name: Optional[str] = None,
    node_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update a graph node by _id.
    Returns updated node or None if not found.
    """
    if not node_id or not isinstance(node_id, str):
        raise ValueError("node_id is required and must be a string")
    
    update_fields = {KEY_UT: int(time.time() * 1000)}
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("name cannot be empty")
        update_fields[KEY_NAME] = name
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
        logger.exception("[graph_node_repo] update_node error: %s", e)
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
        logger.exception("[graph_node_repo] delete_node error: %s", e)
        raise


def _doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to API-friendly dict."""
    out = {
        "name": doc.get(KEY_NAME, ""),
        "app_id": doc.get(KEY_APP_ID, ""),
        "node_type": doc.get(KEY_NODE_TYPE, "entity"),
        "ct": doc.get(KEY_CT, 0),
        "ut": doc.get(KEY_UT, 0),
    }
    if KEY_ID in doc:
        out["id"] = str(doc[KEY_ID])
    return out
