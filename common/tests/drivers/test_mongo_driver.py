import os
import pprint
import unittest
from dataclasses import asdict
from datetime import datetime
from unittest import TestCase

from common.drivers.mongo_driver import MongoDriver

try:
    from app_finance.models.technic_spec_model import TechnicSpecModel
except ImportError:
    TechnicSpecModel = None

# Integration tests require a running MongoDB; skip unless explicitly enabled.
RUN_MONGO_INTEGRATION = os.environ.get("RUN_MONGO_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


@unittest.skipUnless(RUN_MONGO_INTEGRATION, "MongoDB integration tests disabled (set RUN_MONGO_INTEGRATION_TESTS=1 to run)")
class TestMangoDriver(TestCase):
    def setUp(self):
        self.dut = MongoDriver("koi3w9q.mongodb.net", "rongjinzh", "Z6RdcXfmkYUZOgHd", "cluster0", "test")

    def test_ping(self):
        self.dut.ping()

    def test_list_databases(self):
        db_list = self.dut.list_databases()
        print(f"Databases: {db_list}")

    def test_list_collections(self):
        coll_list = self.dut.list_collections()
        print(coll_list)

    def test_create_index(self):
        result = self.dut.create_index("test", [("city", 1), ("age", -1)])
        print(f"create index: {result}")

    def test_delete_index(self):
        self.dut.delete_index("test", "city_1_age_-1")

    def test_list_indexes(self):
        indexes = self.dut.list_indexes("test")
        for index in indexes:
            print(f"index: {index}")

    def test_find_all(self):
        results = self.dut.find_all("test")
        for result in results:
            pprint.pprint(result)

    def test_insert(self):
        user = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "city": "New York",
            "created_at": datetime.now()
        }
        result = self.dut.insert("test", user)
        print(result)

    def test_update(self):
        new_user = {
            "email": "john@yahoo.com",
            "age": 18,
            "city": "Atlanta",
            "created_at": datetime.now()
        }
        result = self.dut.insert_or_update("test", {"name": "John Doe"}, new_user)
        print(result)

    def test_delete(self):
        result = self.dut.delete("test", {"name": "John Doe"})
        print(result)

    def test_list_search_indexes(self):
        index_list = self.dut.list_search_indexes("test")
        for index in index_list:
            print(f"search_index: {index}")

    def test_create_search_index(self):
        result = self.dut.create_vector_search_index("test", "voodoo", 384)
        print(f"create search_index: {result}")

    def test_delete_search_index(self):
        self.dut.delete_search_index("test", "vec_voodoo")


@unittest.skipIf(TechnicSpecModel is None, "app_finance not installed")
class TestTechnicSpecRepo(TestCase):
    def setUp(self):
        self.dut = MongoDriver("koi3w9q.mongodb.net", "rongjinzh", "Z6RdcXfmkYUZOgHd", "cluster0", "tech_xiangshan")

    def test_insert(self):
        # lazy load
        from sentence_transformers import SentenceTransformer

        spec_dict = {
            "field": "s2xlate",
            "feature": "区分 stage",
            "feature_detail": {
                "noS2xlate": 0,
                "allStage": 3,
                "onlyStage1": 1,
                "onlyStage2": 2
            }
        }
        spec_model = TechnicSpecModel(**spec_dict)

        trans = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        spec_model.feature_emvec = trans.encode(spec_model.feature).tolist()
        result = self.dut.insert("spec", asdict(spec_model))
        print(result)

    def test_create_search_index(self):
        result = self.dut.create_vector_search_index("spec", "feature_emvec", 384)
        print(f"create search_index: {result}")

    def test_find_by_cond(self):
        results = self.dut.find_one_by_cond("spec", {"field": "tlb 类型"})
        for result in results:
            pprint.pprint(result)
