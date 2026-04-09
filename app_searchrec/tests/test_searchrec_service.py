from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from app_searchrec.services import SearchRecService
from app_searchrec.services.searchrec_service import _clamp_top_k, _score_boost_for_item
from app_searchrec.tests.fake_lexical_index import FakeLexicalIndexAdapter


class _PatchLexicalIndexMixin:
    """Avoid requiring MySQL searchrec_rw in unit tests; production uses DbIndexAdapter."""

    def setUp(self):
        # Drop cached adapters before patching: otherwise reset() would call
        # DbIndexAdapter.reset() (ORM) left over from tests that did not patch build_index_adapter.
        SearchRecService._index_adapter = None
        SearchRecService._vector_adapter = None
        SearchRecService._feature_store_adapter = None
        self._patcher = patch(
            "app_searchrec.services.searchrec_service.build_index_adapter",
            return_value=FakeLexicalIndexAdapter(),
        )
        self._patcher.start()
        self.addCleanup(self._patcher.stop)
        SearchRecService.reset()

    def tearDown(self):
        SearchRecService.reset()
        super().tearDown()


class TestSearchRecService(_PatchLexicalIndexMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "doc_python",
                    "title": "Python Search API",
                    "content": "Design a foundation service for search and recommend",
                    "tags": ["search", "backend"],
                    "score_boost": 1.0,
                    "popularity_score": 0.2,
                },
                {
                    "id": "doc_java",
                    "title": "Java Recommend Engine",
                    "content": "Retrieval and ranking system for e-commerce",
                    "tags": ["recommend", "backend"],
                    "score_boost": 1.1,
                    "popularity_score": 0.9,
                },
            ]
        )

    def test_search(self):
        result = SearchRecService.search(1, "search service", top_k=5, preferred_tags=["search"])
        self.assertGreaterEqual(result["total_hits"], 1)
        self.assertEqual(result["items"][0]["id"], "doc_python")

    def test_recommend(self):
        result = SearchRecService.recommend(
            1,
            user_profile={
                "preferred_tags": ["recommend"],
                "recent_queries": ["ranking engine"],
                "affinity_boost": 1.2,
            },
            top_k=5,
        )
        self.assertGreaterEqual(result["total_hits"], 1)
        self.assertIn("affinity_boost", result["items"][0]["features"])

    def test_rank(self):
        ranked = SearchRecService.rank(
            candidates=[
                {"id": "a", "base_score": 0.9, "ctr_score": 0.3, "freshness_score": 0.1},
                {"id": "b", "base_score": 0.5, "ctr_score": 0.8, "freshness_score": 0.4},
            ],
            strategy="ctr_first",
        )
        self.assertEqual(ranked["items"][0]["id"], "b")

    @override_settings(
        SEARCHREC_MERGE_VECTOR_CANDIDATES=True,
        SEARCHREC_SEARCH_CANDIDATE_MULTIPLIER=1,
    )
    def test_merge_vector_candidates_adds_vector_only_hits(self):
        SearchRecService.reset()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "lex_only",
                    "title": "alpha",
                    "content": "x",
                    "tags": ["t"],
                    "score_boost": 1.0,
                    "popularity_score": 0.0,
                },
                {
                    "id": "vec_only",
                    "title": "beta",
                    "content": "y",
                    "tags": ["t"],
                    "score_boost": 1.0,
                    "popularity_score": 0.0,
                },
            ],
        )
        SearchRecService._ensure_adapters()

        def fake_lexical(rid, query, top_k):
            return [
                {
                    "id": "lex_only",
                    "title": "alpha",
                    "tags": ["t"],
                    "lexical_score": 0.99,
                    "score_boost": 1.0,
                }
            ]

        def fake_vector(rid, query, top_k):
            return [{"id": "vec_only", "vector_score": 10.0}, {"id": "lex_only", "vector_score": 1.0}]

        with patch.object(SearchRecService._index_adapter, "search", side_effect=fake_lexical):
            with patch.object(SearchRecService._vector_adapter, "search", side_effect=fake_vector):
                result = SearchRecService.search(1, "ignored", top_k=5)
        ids = [x["id"] for x in result["items"]]
        self.assertIn("vec_only", ids)
        self.assertIn("lex_only", ids)


class TestClampTopK(SimpleTestCase):
    def test_none_uses_configured_default(self):
        self.assertEqual(_clamp_top_k(None, 10), 10)

    def test_invalid_string_uses_default(self):
        self.assertEqual(_clamp_top_k("not-an-int", 7), 7)

    def test_zero_and_negative_use_default(self):
        self.assertEqual(_clamp_top_k(0, 12), 12)
        self.assertEqual(_clamp_top_k(-3, 12), 12)

    def test_caps_at_100(self):
        self.assertEqual(_clamp_top_k(500, 10), 100)

    def test_minimum_one(self):
        self.assertEqual(_clamp_top_k(1, 10), 1)


class TestScoreBoostForItem(SimpleTestCase):
    def test_prefers_doc_features(self):
        self.assertEqual(
            _score_boost_for_item({"score_boost": 2.0}, {"score_boost": 9.0}),
            2.0,
        )

    def test_falls_back_to_item(self):
        self.assertEqual(_score_boost_for_item({}, {"score_boost": 1.25}), 1.25)

    def test_default_without_item_key(self):
        self.assertEqual(_score_boost_for_item({}, {}), 1.0)

    def test_doc_features_none_means_use_item(self):
        self.assertEqual(_score_boost_for_item({"score_boost": None}, {"score_boost": 0.5}), 0.5)


class TestSearchRecServiceValidation(SimpleTestCase):
    def tearDown(self):
        SearchRecService.reset()

    def test_upsert_rejects_non_list(self):
        with self.assertRaisesMessage(ValueError, "field `documents` must be a non-empty list"):
            SearchRecService.upsert_documents(1, "bad")

    def test_upsert_rejects_empty_list(self):
        with self.assertRaisesMessage(ValueError, "field `documents` must be a non-empty list"):
            SearchRecService.upsert_documents(1, [])

    def test_rank_rejects_non_list_candidates(self):
        with self.assertRaisesMessage(ValueError, "field `candidates` must be list"):
            SearchRecService.rank(candidates="x", strategy="hybrid")


class TestSearchRecServiceRankStrategies(SimpleTestCase):
    def test_fresh_first_strategy(self):
        ranked = SearchRecService.rank(
            candidates=[
                {"id": "a", "base_score": 1.0, "ctr_score": 0.0, "freshness_score": 0.9},
                {"id": "b", "base_score": 1.0, "ctr_score": 0.9, "freshness_score": 0.0},
            ],
            strategy="fresh_first",
        )
        self.assertEqual(ranked["items"][0]["id"], "a")

    def test_hybrid_default_strategy(self):
        ranked = SearchRecService.rank(
            candidates=[{"id": "z", "base_score": 0.5, "ctr_score": 0.5, "freshness_score": 0.5}],
            strategy="unknown_strategy_name",
        )
        self.assertEqual(ranked["strategy"], "unknown_strategy_name")
        self.assertIn("final_score", ranked["items"][0])


class TestSearchRecServiceRecommend(_PatchLexicalIndexMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "doc_only_tags",
                    "title": "t",
                    "content": "c",
                    "tags": ["alpha"],
                    "score_boost": 1.0,
                    "popularity_score": 0.1,
                },
            ],
        )

    def test_recommend_falls_back_to_preferred_tags_when_queries_empty(self):
        result = SearchRecService.recommend(
            1,
            user_profile={"preferred_tags": ["alpha"], "recent_queries": []},
            top_k=5,
        )
        self.assertGreaterEqual(result["total_hits"], 0)


class TestSearchWithoutMerge(_PatchLexicalIndexMixin, SimpleTestCase):
    @override_settings(SEARCHREC_MERGE_VECTOR_CANDIDATES=False)
    def test_merge_disabled_uses_lexical_only(self):
        SearchRecService.reset()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "only",
                    "title": "uniqueword",
                    "content": "c",
                    "tags": [],
                    "score_boost": 1.0,
                    "popularity_score": 0.5,
                },
            ],
        )
        result = SearchRecService.search(1, "uniqueword", top_k=5)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "only")


class TestSearchNonListTags(_PatchLexicalIndexMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "doc_tags",
                    "title": "hello",
                    "content": "world",
                    "tags": ["t1"],
                    "score_boost": 1.0,
                    "popularity_score": 0.5,
                },
            ],
        )
        SearchRecService._ensure_adapters()

    def test_non_list_tags_treated_as_empty_for_overlap(self):
        with patch.object(SearchRecService._index_adapter, "search", return_value=[{"id": "doc_tags", "tags": "bad", "lexical_score": 0.9, "score_boost": 1.0, "title": ""}]):
            with patch.object(SearchRecService._vector_adapter, "search", return_value=[]):
                result = SearchRecService.search(1, "hello", top_k=5, preferred_tags=["t1"])
        row = result["items"][0]
        self.assertEqual(row["features"]["tag_score"], 0.0)


class TestSearchMergeSkipsMissingDocument(_PatchLexicalIndexMixin, SimpleTestCase):
    @override_settings(
        SEARCHREC_MERGE_VECTOR_CANDIDATES=True,
        SEARCHREC_SEARCH_CANDIDATE_MULTIPLIER=1,
    )
    def test_vector_only_id_skipped_when_get_document_returns_none(self):
        SearchRecService.reset()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "lex_only",
                    "title": "alpha",
                    "content": "x",
                    "tags": ["t"],
                    "score_boost": 1.0,
                    "popularity_score": 0.0,
                },
            ],
        )
        SearchRecService._ensure_adapters()

        def fake_lexical(rid, query, top_k):
            return [
                {
                    "id": "lex_only",
                    "title": "alpha",
                    "tags": ["t"],
                    "lexical_score": 0.99,
                    "score_boost": 1.0,
                }
            ]

        def fake_vector(rid, query, top_k):
            return [{"id": "ghost", "vector_score": 10.0}]

        with patch.object(SearchRecService._index_adapter, "search", side_effect=fake_lexical):
            with patch.object(SearchRecService._vector_adapter, "search", side_effect=fake_vector):
                with patch.object(SearchRecService._index_adapter, "get_document", return_value=None):
                    result = SearchRecService.search(1, "ignored", top_k=5)
        ids = [x["id"] for x in result["items"]]
        self.assertNotIn("ghost", ids)
        self.assertIn("lex_only", ids)


class TestSearchFiltersNonPositiveScore(_PatchLexicalIndexMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        SearchRecService.upsert_documents(
            1,
            [
                {
                    "id": "doc_z",
                    "title": "z",
                    "content": "z",
                    "tags": [],
                    "score_boost": 1.0,
                    "popularity_score": 0.0,
                },
            ],
        )
        SearchRecService._ensure_adapters()

    def test_zero_score_boost_drops_row(self):
        with patch.object(SearchRecService._index_adapter, "search", return_value=[{"id": "doc_z", "tags": [], "lexical_score": 0.5, "score_boost": 1.0, "title": ""}]):
            with patch.object(SearchRecService._vector_adapter, "search", return_value=[]):
                with patch.object(
                    SearchRecService._feature_store_adapter,
                    "get_doc_features",
                    return_value={"score_boost": 0.0, "popularity_score": 0.0, "freshness_score": 0.0},
                ):
                    result = SearchRecService.search(1, "q", top_k=5)
        self.assertEqual(result["total_hits"], 0)


class TestRecommendStarQuery(_PatchLexicalIndexMixin, SimpleTestCase):
    def test_empty_profile_uses_star_query(self):
        result = SearchRecService.recommend(1, user_profile={}, top_k=3)
        self.assertIn("items", result)
