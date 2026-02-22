"""
Tests for summary repository (MongoDB); validation and edge cases. Generated.
Uses mocked Atlas client and in-memory collection behavior.
"""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from common.consts.query_const import LIMIT_LIST

from app_know.repos.summary_repo import (
    save_summary,
    get_summary,
    list_summaries,
    delete_by_knowledge_id,
    search_summaries_by_text,
    SUMMARY_STORAGE_MAX_LEN,
    QUERY_SEARCH_MAX_LEN,
    KEY_KNOWLEDGE_ID,
    KEY_APP_ID,
    KEY_SUMMARY,
    KEY_CT,
    KEY_UT,
    KEY_ID,
)


def _make_mock_coll():
    """In-memory list to simulate collection."""
    store = []

    def find_one(query):
        for d in store:
            if all(d.get(k) == v for k, v in query.items()):
                return dict(d)
        return None

    def insert_one(doc):
        doc[KEY_ID] = len(store) + 1
        store.append(dict(doc))

    def update_one(filter_q, update):
        for d in store:
            if all(d.get(k) == v for k, v in filter_q.items()):
                if "$set" in update:
                    d.update(update["$set"])
                return MagicMock(modified_count=1)
        return MagicMock(modified_count=0)

    def find(query):
        class Cursor:
            def __init__(self, q):
                self._query = q
                self._sort_key = KEY_UT
                self._sort_dir = -1
                self._skip = 0
                self._limit = 100

            def sort(self, key, direction):
                self._sort_key = key
                self._sort_dir = direction
                return self

            def skip(self, n):
                self._skip = n
                return self

            def limit(self, n):
                self._limit = n
                return self

            def __iter__(self):
                filtered = [d for d in store if all(d.get(k) == v for k, v in self._query.items())]
                filtered.sort(key=lambda x: x.get(self._sort_key, 0), reverse=(self._sort_dir == -1))
                for d in filtered[self._skip : self._skip + self._limit]:
                    yield d

        return Cursor(query)

    def count_documents(query):
        return sum(1 for d in store if all(d.get(k) == v for k, v in query.items()))

    def delete_many(query):
        to_remove = [d for d in store if all(d.get(k) == v for k, v in query.items())]
        for d in to_remove:
            store.remove(d)
        return MagicMock(deleted_count=len(to_remove))

    def create_index(*args, **kwargs):
        pass

    coll = MagicMock()
    coll.find_one = find_one
    coll.insert_one = insert_one
    coll.update_one = update_one
    coll.find = find
    coll.count_documents = count_documents
    coll.delete_many = delete_many
    coll.create_index = create_index
    return coll, store


class SummaryRepoTest(TestCase):
    """Tests for summary repo with mocked Atlas."""

    def setUp(self):
        self.mock_coll, self.store = _make_mock_coll()
        self.mock_atlas = MagicMock()
        self.mock_atlas.get_collection.return_value = self.mock_coll

    def test_save_summary_insert(self):
        out = save_summary(
            knowledge_id=1,
            summary="My summary",
            app_id="app1",
            atlas=self.mock_atlas,
        )
        self.assertEqual(out["knowledge_id"], 1)
        self.assertEqual(out["summary"], "My summary")
        self.assertEqual(out["app_id"], "app1")
        self.assertIn("id", out)
        self.assertEqual(len(self.store), 1)

    def test_save_summary_upsert(self):
        save_summary(knowledge_id=1, summary="First", app_id="app1", atlas=self.mock_atlas)
        out = save_summary(knowledge_id=1, summary="Second", app_id="app1", atlas=self.mock_atlas)
        self.assertEqual(out["summary"], "Second")
        self.assertEqual(len(self.store), 1)

    def test_save_summary_validation_invalid_knowledge_id(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=0, summary="x", app_id="a", atlas=self.mock_atlas)
        self.assertIn("positive integer", str(ctx.exception))
        with self.assertRaises(ValueError):
            save_summary(knowledge_id=-1, summary="x", app_id="a", atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            save_summary(knowledge_id=None, summary="x", app_id="a", atlas=self.mock_atlas)

    def test_save_summary_validation_empty_app_id(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary="x", app_id="  ", atlas=self.mock_atlas)
        self.assertIn("app_id", str(ctx.exception))

    def test_save_summary_validation_summary_none(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary=None, app_id="a", atlas=self.mock_atlas)
        self.assertIn("summary", str(ctx.exception))

    def test_save_summary_validation_summary_not_string(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(knowledge_id=1, summary=123, app_id="a", atlas=self.mock_atlas)
        self.assertIn("summary", str(ctx.exception))

    def test_save_summary_validation_summary_too_long(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(
                knowledge_id=1,
                summary="x" * (SUMMARY_STORAGE_MAX_LEN + 1),
                app_id="a",
                atlas=self.mock_atlas,
            )
        self.assertIn("exceed", str(ctx.exception))

    def test_save_summary_validation_source_not_string(self):
        with self.assertRaises(ValueError) as ctx:
            save_summary(
                knowledge_id=1, summary="x", app_id="a", source=123, atlas=self.mock_atlas
            )
        self.assertIn("source", str(ctx.exception))

    def test_save_summary_empty_string_summary_allowed(self):
        out = save_summary(
            knowledge_id=1, summary="", app_id="app1", atlas=self.mock_atlas
        )
        self.assertEqual(out["summary"], "")
        self.assertEqual(len(self.store), 1)

    def test_get_summary(self):
        save_summary(knowledge_id=2, summary="Found", app_id="app2", atlas=self.mock_atlas)
        out = get_summary(knowledge_id=2, app_id="app2", atlas=self.mock_atlas)
        self.assertIsNotNone(out)
        self.assertEqual(out["summary"], "Found")

    def test_get_summary_not_found(self):
        out = get_summary(knowledge_id=999, atlas=self.mock_atlas)
        self.assertIsNone(out)

    def test_get_summary_invalid_knowledge_id_returns_none(self):
        self.assertIsNone(get_summary(knowledge_id=0, atlas=self.mock_atlas))
        self.assertIsNone(get_summary(knowledge_id=-1, atlas=self.mock_atlas))

    def test_list_summaries(self):
        save_summary(knowledge_id=1, summary="S1", app_id="app1", atlas=self.mock_atlas)
        save_summary(knowledge_id=2, summary="S2", app_id="app1", atlas=self.mock_atlas)
        items, total = list_summaries(app_id="app1", offset=0, limit=10, atlas=self.mock_atlas)
        self.assertEqual(total, 2)
        self.assertEqual(len(items), 2)

    def test_list_summaries_pagination(self):
        save_summary(knowledge_id=1, summary="S1", app_id="a", atlas=self.mock_atlas)
        save_summary(knowledge_id=2, summary="S2", app_id="a", atlas=self.mock_atlas)
        save_summary(knowledge_id=3, summary="S3", app_id="a", atlas=self.mock_atlas)
        items, total = list_summaries(app_id="a", offset=1, limit=1, atlas=self.mock_atlas)
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 1)

    def test_list_summaries_validation(self):
        with self.assertRaises(ValueError):
            list_summaries(offset=-1, limit=10, atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            list_summaries(offset=0, limit=0, atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            list_summaries(offset=0, limit=LIMIT_LIST + 1, atlas=self.mock_atlas)
        with self.assertRaises(ValueError) as ctx:
            list_summaries(offset=None, limit=10, atlas=self.mock_atlas)
        self.assertIn("offset", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            list_summaries(offset=0, limit=None, atlas=self.mock_atlas)
        self.assertIn("limit", str(ctx.exception))

    def test_delete_by_knowledge_id(self):
        save_summary(knowledge_id=10, summary="X", app_id="a", atlas=self.mock_atlas)
        save_summary(knowledge_id=10, summary="Y", app_id="b", atlas=self.mock_atlas)
        n = delete_by_knowledge_id(knowledge_id=10, atlas=self.mock_atlas)
        self.assertEqual(n, 2)
        self.assertIsNone(get_summary(knowledge_id=10, app_id="a", atlas=self.mock_atlas))

    def test_delete_by_knowledge_id_invalid_returns_zero(self):
        n = delete_by_knowledge_id(knowledge_id=0, atlas=self.mock_atlas)
        self.assertEqual(n, 0)

    def test_search_summaries_by_text_validation(self):
        with self.assertRaises(ValueError) as ctx:
            search_summaries_by_text(query=None, atlas=self.mock_atlas)
        self.assertIn("required", str(ctx.exception))
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="", atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="  ", atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query=123, atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="x", limit=0, atlas=self.mock_atlas)
        with self.assertRaises(ValueError):
            search_summaries_by_text(query="x", limit=LIMIT_LIST + 1, atlas=self.mock_atlas)
        with self.assertRaises(ValueError) as ctx:
            search_summaries_by_text(
                query="x" * (QUERY_SEARCH_MAX_LEN + 1),
                limit=10,
                atlas=self.mock_atlas,
            )
        self.assertIn("exceed", str(ctx.exception).lower())

    def test_search_summaries_by_text_success(self):
        def mock_find(query):
            class Cursor:
                def limit(self, n):
                    return self
                def __iter__(self):
                    yield {
                        KEY_KNOWLEDGE_ID: 2,
                        KEY_SUMMARY: "Keyword match here",
                        KEY_APP_ID: "app1",
                        KEY_CT: 1000,
                        KEY_UT: 1000,
                        KEY_ID: "oid1",
                    }
            return Cursor()
        self.mock_coll.find = mock_find
        items = search_summaries_by_text(query="keyword", limit=10, atlas=self.mock_atlas)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["knowledge_id"], 2)
        self.assertEqual(items[0]["score"], 1.0)
        self.assertIn("Keyword", items[0]["summary"])

    def test_search_summaries_by_text_regex_special_chars_escaped(self):
        """Query with regex special chars is escaped and used safely (no crash)."""
        seen_query = []

        def mock_find(query):
            seen_query.append(query)
            class Cursor:
                def limit(self, n):
                    return self
                def __iter__(self):
                    return iter([])
            return Cursor()
        self.mock_coll.find = mock_find
        items = search_summaries_by_text(
            query="[.()*+?^$|\\",
            limit=10,
            atlas=self.mock_atlas,
        )
        self.assertEqual(items, [])
        self.assertEqual(len(seen_query), 1)
        self.assertIn(KEY_SUMMARY, seen_query[0])
        self.assertIn("$regex", seen_query[0][KEY_SUMMARY])
