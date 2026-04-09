"""Unit tests for app_searchrec adapters (memory vector/feature backends and pure helpers)."""

from django.test import SimpleTestCase, override_settings

from app_searchrec.adapters.feature_store import (
    FeastFeatureStoreAdapter,
    MemoryFeatureStoreAdapter,
    build_feature_store_adapter,
)
from app_searchrec.adapters.index_store import (
    DbIndexAdapter,
    OpenSearchIndexAdapter,
    _hit_doc_id,
    _search_response_hits,
    _tokenize,
    build_index_adapter,
)
from app_searchrec.adapters.vector_store import (
    MemoryVectorAdapter,
    MilvusVectorAdapter,
    QdrantVectorAdapter,
    _milvus_vector_score,
    _qdrant_doc_id,
    build_vector_adapter,
)
from app_searchrec.tests.fake_lexical_index import FakeLexicalIndexAdapter


class TestIndexStoreHelpers(SimpleTestCase):
    def test_tokenize_splits_words(self):
        self.assertEqual(_tokenize("Hello 世界"), ["hello", "世界"])

    def test_tokenize_empty(self):
        self.assertEqual(_tokenize(""), [])

    def test_search_response_hits_invalid(self):
        self.assertEqual(_search_response_hits(None), [])
        self.assertEqual(_search_response_hits({"hits": "bad"}), [])
        self.assertEqual(_search_response_hits({"hits": {"hits": "bad"}}), [])

    def test_search_response_hits_ok(self):
        data = {"hits": {"hits": [{"_id": "1"}]}}
        self.assertEqual(len(_search_response_hits(data)), 1)

    def test_hit_doc_id_prefers_source_id(self):
        self.assertEqual(_hit_doc_id({"id": "src"}, {"_id": "es"}), "src")

    def test_hit_doc_id_falls_back_to_es_id(self):
        self.assertEqual(_hit_doc_id({}, {"_id": "es_only"}), "es_only")


class TestVectorStoreHelpers(SimpleTestCase):
    def test_milvus_vector_score_prefers_score(self):
        self.assertEqual(_milvus_vector_score({"score": 2.0, "vector_score": 9.0}), 2.0)

    def test_milvus_vector_score_uses_vector_score(self):
        self.assertEqual(_milvus_vector_score({"vector_score": 3.5}), 3.5)

    def test_qdrant_doc_id_payload_wins(self):
        self.assertEqual(_qdrant_doc_id({"id": "p"}, {"id": "outer"}), "p")

    def test_qdrant_doc_id_item_fallback(self):
        self.assertEqual(_qdrant_doc_id({}, {"id": "outer"}), "outer")


class TestFakeLexicalIndexAdapter(SimpleTestCase):
    """Same validation rules as DbIndexAdapter for tags / id (test double for CI without MySQL)."""

    def test_upsert_requires_tags_list(self):
        adapter = FakeLexicalIndexAdapter()
        with self.assertRaisesMessage(ValueError, "field `tags` must be list"):
            adapter.upsert_documents(
                [{"id": "a", "title": "t", "content": "c", "tags": "not-a-list"}]
            )

    def test_search_star_returns_empty(self):
        adapter = FakeLexicalIndexAdapter()
        adapter.upsert_documents([{"id": "a", "title": "hello world", "content": "c", "tags": ["t"]}])
        self.assertEqual(adapter.search("*", top_k=10), [])


class TestMemoryVectorAdapter(SimpleTestCase):
    def setUp(self):
        self.adapter = MemoryVectorAdapter()

    def test_reset_clears_state(self):
        self.adapter.upsert_documents([{"id": "a", "title": "t", "content": "c", "tags": []}])
        self.assertEqual(len(self.adapter._vectors), 1)
        self.adapter.reset()
        self.assertEqual(len(self.adapter._vectors), 0)

    def test_search_star_returns_empty(self):
        self.adapter.upsert_documents([{"id": "a", "title": "hello", "content": "x", "tags": []}])
        self.assertEqual(self.adapter.search("*", top_k=10), [])

    def test_upsert_skips_blank_id(self):
        self.adapter.upsert_documents([{"id": "", "title": "x", "content": "y", "tags": []}])
        self.assertEqual(len(self.adapter._vectors), 0)


class TestMemoryFeatureStoreAdapter(SimpleTestCase):
    def setUp(self):
        self.adapter = MemoryFeatureStoreAdapter()

    def test_get_user_features_none_profile(self):
        out = self.adapter.get_user_features(None)
        self.assertEqual(out["preferred_tags"], [])
        self.assertEqual(out["recent_queries"], [])
        self.assertEqual(out["affinity_boost"], 1.0)

    def test_get_user_features_non_list_tags_coerced(self):
        out = self.adapter.get_user_features({"preferred_tags": "x", "recent_queries": 1})
        self.assertEqual(out["preferred_tags"], [])
        self.assertEqual(out["recent_queries"], [])


class TestBuildAdapters(SimpleTestCase):
    @override_settings(
        SEARCHREC_OPENSEARCH_ENABLED=True,
        SEARCHREC_OPENSEARCH_URL="http://localhost:9200",
    )
    def test_build_index_opensearch_when_enabled(self):
        self.assertIsInstance(build_index_adapter(), OpenSearchIndexAdapter)

    @override_settings(SEARCHREC_OPENSEARCH_ENABLED=False)
    def test_build_index_db_when_opensearch_disabled(self):
        self.assertIsInstance(build_index_adapter(), DbIndexAdapter)

    @override_settings(
        SEARCHREC_MILVUS_ENABLED=True,
        SEARCHREC_QDRANT_ENABLED=False,
        SEARCHREC_MILVUS_ENDPOINT="http://localhost:19530",
    )
    def test_build_vector_milvus_when_enabled(self):
        self.assertIsInstance(build_vector_adapter(), MilvusVectorAdapter)

    @override_settings(
        SEARCHREC_MILVUS_ENABLED=False,
        SEARCHREC_QDRANT_ENABLED=True,
        SEARCHREC_QDRANT_URL="http://localhost:6333",
    )
    def test_build_vector_qdrant_when_enabled(self):
        self.assertIsInstance(build_vector_adapter(), QdrantVectorAdapter)

    @override_settings(SEARCHREC_MILVUS_ENABLED=False, SEARCHREC_QDRANT_ENABLED=False)
    def test_build_vector_memory_when_no_remote(self):
        self.assertIsInstance(build_vector_adapter(), MemoryVectorAdapter)

    @override_settings(SEARCHREC_MILVUS_ENABLED=True, SEARCHREC_QDRANT_ENABLED=True)
    def test_build_vector_raises_when_milvus_and_qdrant_both_enabled(self):
        with self.assertRaisesMessage(
            ValueError,
            "SEARCHREC_MILVUS_ENABLED and SEARCHREC_QDRANT_ENABLED cannot both be true",
        ):
            build_vector_adapter()

    @override_settings(
        SEARCHREC_FEAST_ENABLED=True,
        SEARCHREC_FEAST_ONLINE_URL="http://localhost:6566",
    )
    def test_build_feature_feast_when_enabled(self):
        self.assertIsInstance(build_feature_store_adapter(), FeastFeatureStoreAdapter)

    @override_settings(SEARCHREC_FEAST_ENABLED=False)
    def test_build_feature_memory_when_feast_disabled(self):
        self.assertIsInstance(build_feature_store_adapter(), MemoryFeatureStoreAdapter)
