import logging
import os
from typing import TYPE_CHECKING

from pymongo import MongoClient

from common.components.singleton import Singleton
from common.consts.string_const import EMPTY_STRING

if TYPE_CHECKING:
    from pymongo.collection import Collection


logger = logging.getLogger(__name__)

# Read SSL and proxy settings from environment
MONGO_TLS_INSECURE = os.environ.get("MONGO_TLS_INSECURE", "false").lower() == "true"
MONGO_PROXY_HOST = os.environ.get("MONGO_PROXY_HOST", "")
MONGO_PROXY_PORT = os.environ.get("MONGO_PROXY_PORT", "")

# Check pymongo version for proxy support
import pymongo
PYMONGO_VERSION = tuple(int(x) for x in pymongo.version.split(".")[:2])
PYMONGO_4_PLUS = PYMONGO_VERSION >= (4, 0)


def _build_vector_index_name(attr_name: str):
    return f"vec_{attr_name}"


class MongoDriver(Singleton):
    def __init__(self, host: str, username: str, password: str, cluster: str, db_name: str) -> None:
        uri = f"mongodb+srv://{username}:{password}@{cluster}.{host}/?retryWrites=true&w=majority&appName=Cluster0"
        
        client_options = {
            "tls": True,
            "serverSelectionTimeoutMS": 10000,
        }
        
        if MONGO_TLS_INSECURE:
            client_options["tlsAllowInvalidCertificates"] = True
            logger.warning("[MongoDriver] TLS certificate validation disabled (insecure)")
        
        if MONGO_PROXY_HOST and MONGO_PROXY_PORT:
            if PYMONGO_4_PLUS:
                client_options["proxyHost"] = MONGO_PROXY_HOST
                client_options["proxyPort"] = int(MONGO_PROXY_PORT)
                logger.info("[MongoDriver] Using proxy: %s:%s", MONGO_PROXY_HOST, MONGO_PROXY_PORT)
            else:
                logger.warning(
                    "[MongoDriver] Proxy configured but pymongo %s does not support it. "
                    "Please upgrade: pip install 'pymongo>=4.0'",
                    pymongo.version
                )
        
        self._client = MongoClient(uri, **client_options)
        self._db = self._client[db_name]
        try:
            self.ping()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def __del__(self):
        print('---- mongo driver closed ----')
        if hasattr(self, '_client') and self._client is not None:
            self._client.close()

    def ping(self) -> None:
        try:
            self._client.admin.command('ping')
            return
        except Exception as e:
            logger.exception(e)
            raise

    def create_or_get_collection(self, coll_name: str) -> "Collection":
        """
        Create or get collection with optional settings
        """
        try:
            collection = self._db[coll_name]
            return collection
        except Exception as e:
            logger.exception(e)

    def add_field_to_collection(self, coll_name: str, field_name: str, default_value=None):
        """
        Add a field to the collection if it does not exist
        """
        try:
            coll = self.create_or_get_collection(coll_name)
            return coll.update_many({}, {"$set": {field_name: default_value}})
        except Exception as e:
            logger.exception(e)
            return False

    def list_databases(self) -> list[str]:
        """
        List all databases
        """
        try:
            db_list = self._client.list_database_names()
            return db_list
        except Exception as e:
            logger.exception(e)

    def list_collections(self) -> list[str]:
        """
        List all collections in database
        """
        try:
            coll_list = self._db.list_collection_names()
            return coll_list
        except Exception as e:
            logger.exception(e)

    def list_indexes(self, coll_name: str):
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.list_indexes()
            return result
        except Exception as e:
            logger.exception(e)

    def create_index(self, coll_name: str, index_exprs: list[tuple[str, int]]):
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.create_index(index_exprs)
            return result
        except Exception as e:
            logger.exception(e)

    def delete_index(self, coll_name: str, index_name: str):
        try:
            coll = self.create_or_get_collection(coll_name)
            coll.drop_index(index_name)
        except Exception as e:
            logger.exception(e)

    def find_all(self, coll_name: str):
        try:
            coll = self.create_or_get_collection(coll_name)
            datas = coll.find()
            return datas
        except Exception as e:
            logger.exception(e)

    def find_one_by_cond(self, coll_name: str, cond: dict):
        try:
            coll = self.create_or_get_collection(coll_name)
            datas = coll.find_one(cond)
            return datas
        except Exception as e:
            logger.exception(e)

    def insert(self, coll_name: str, data: dict) -> str:
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.insert_one(data)
            return str(result.inserted_id)
        except Exception as e:
            logger.exception(e)
            return EMPTY_STRING

    def batch_insert(self, coll_name: str, datas: list[dict]) -> list[int]:
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.insert_many(datas)
            return result.inserted_ids
        except Exception as e:
            logger.exception(e)

    def insert_or_update(self, coll_name: str, cond: dict, new_data: dict) -> str:
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.update_one(cond,
                                     {
                                         "$set": new_data
                                     },
                                     upsert=True)
            return str(result.upserted_id)
        except Exception as e:
            logger.exception(e)

    def delete(self, coll_name: str, cond: dict):
        try:
            coll = self.create_or_get_collection(coll_name)
            result = coll.delete_many(cond)
            return result
        except Exception as e:
            logger.exception(e)

    def list_search_indexes(self, coll_name: str) -> list:
        try:
            coll = self.create_or_get_collection(coll_name)
            indexes = coll.list_search_indexes()
            return list(indexes)
        except Exception as e:
            logger.exception(e)

    def create_vector_search_index(self, coll_name: str, attr_name: str, dim_num: int):
        try:
            from pymongo.operations import SearchIndexModel
        except ImportError:
            logger.error("[MongoDriver] SearchIndexModel requires pymongo >= 4.x")
            return None
        try:
            coll = self.create_or_get_collection(coll_name)
            vector_index = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "numDimensions": dim_num,
                            "path": attr_name,
                            "similarity": "cosine"
                        }
                    ]
                },
                name=_build_vector_index_name(attr_name),
                type="vectorSearch",
            )
            result = coll.create_search_index(model=vector_index)
            return result
        except Exception as e:
            logger.exception(e)

    def delete_search_index(self, coll_name: str, index_name: str):
        try:
            coll = self.create_or_get_collection(coll_name)
            coll.drop_search_index(index_name)
        except Exception as e:
            logger.exception(e)

    def vector_search(self,
                      coll_name: str,
                      attr_name: str,
                      embedded_vec: list[float],
                      cand_num: int = 50,
                      limit: int = 3,
                      proj: dict = None) -> list:
        # check arguments
        if proj is None:
            proj = {}
        # prepare data
        pipeline = [
            {
                '$vectorSearch': {
                    "index": _build_vector_index_name(attr_name),
                    "path": attr_name,
                    "queryVector": embedded_vec,
                    "numCandidates": min(max(limit * 20, cand_num), 10000),
                    "limit": limit,
                }
            }, {
                '$project': proj
            }
        ]
        # query data
        try:
            coll = self.create_or_get_collection(coll_name)
            results = coll.aggregate(pipeline)
            return list(results)
        except Exception as e:
            logger.exception(e)
