from django.test import SimpleTestCase

from app_searchrec.services import SearchRecService


class TestSearchRecService(SimpleTestCase):
    def setUp(self):
        SearchRecService.reset()
        SearchRecService.upsert_documents(
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
        result = SearchRecService.search("search service", top_k=5, preferred_tags=["search"])
        self.assertGreaterEqual(result["total_hits"], 1)
        self.assertEqual(result["items"][0]["id"], "doc_python")

    def test_recommend(self):
        result = SearchRecService.recommend(
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
