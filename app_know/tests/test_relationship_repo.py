"""
Tests for relationship repo (Neo4j persistence, validation, and edge cases).
_get_neo4j_driver is mocked so no real Neo4j connection is used. Generated.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from app_know.models.relationships import (
    RelationshipCreateInput,
    RelationshipQueryInput,
)
from app_know.repos import relationship_repo


class RelationshipRepoTest(TestCase):
    def setUp(self):
        self.patcher = patch.object(relationship_repo, '_get_neo4j_driver')
        self.mock_get_driver = self.patcher.start()
        self.mock_driver = MagicMock()
        self.mock_get_driver.return_value = self.mock_driver

    def tearDown(self):
        self.patcher.stop()
        relationship_repo._neo4j_driver = None

    def test_create_relationship_knowledge_entity_creates_nodes_and_rel(self):
        self.mock_driver.find_node.side_effect = [None, None]
        mock_start = MagicMock()
        mock_end = MagicMock()
        self.mock_driver.create_node.side_effect = [mock_start, mock_end]
        mock_rel = MagicMock()
        self.mock_driver.create_edge.return_value = mock_rel
        self.mock_driver.find_an_edge.return_value = None

        inp = RelationshipCreateInput(
            app_id="myapp",
            relationship_type="knowledge_entity",
            source_knowledge_id=1,
            entity_type="user",
            entity_id="e1",
            properties={"w": 1},
        )
        rel, start, end = relationship_repo.create_relationship(inp)
        self.assertEqual(rel, mock_rel)
        self.assertEqual(self.mock_driver.create_node.call_count, 2)
        self.mock_driver.create_edge.assert_called_once_with(
            mock_start, mock_end, "RELATES_TO_ENTITY", {"app_id": "myapp", "w": 1}
        )

    def test_create_relationship_knowledge_entity_requires_entity_type_and_id(self):
        inp = RelationshipCreateInput(
            app_id="myapp",
            relationship_type="knowledge_entity",
            source_knowledge_id=1,
        )
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.create_relationship(inp)
        self.assertIn("entity_type", str(ctx.exception).lower())

        inp2 = RelationshipCreateInput(
            app_id="myapp",
            relationship_type="knowledge_entity",
            source_knowledge_id=1,
            entity_type="user",
        )
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.create_relationship(inp2)
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_get_relationship_by_id_not_found(self):
        mock_cursor = MagicMock()
        mock_cursor.single.return_value = None
        self.mock_driver.run.return_value = mock_cursor

        out = relationship_repo.get_relationship_by_id("myapp", 999)
        self.assertIsNone(out)
        self.mock_driver.run.assert_called_once()

    def test_get_relationship_by_id_app_id_mismatch_returns_none(self):
        mock_rel = MagicMock()
        mock_rel.get.return_value = "otherapp"
        mock_cursor = MagicMock()
        mock_cursor.single.return_value = {"r": mock_rel}
        self.mock_driver.run.return_value = mock_cursor

        out = relationship_repo.get_relationship_by_id("myapp", 1)
        self.assertIsNone(out)

    def test_get_relationship_by_id_success(self):
        mock_rel = MagicMock()
        mock_rel.get.side_effect = lambda k: "myapp" if k == "app_id" else None
        mock_cursor = MagicMock()
        mock_cursor.single.return_value = {"r": mock_rel}
        self.mock_driver.run.return_value = mock_cursor

        out = relationship_repo.get_relationship_by_id("myapp", 1)
        self.assertIs(mock_rel, out)

    def test_update_relationship_by_id_not_found(self):
        mock_cursor = MagicMock()
        mock_cursor.single.return_value = None
        self.mock_driver.run.return_value = mock_cursor

        out = relationship_repo.update_relationship_by_id("myapp", 999, {"k": "v"})
        self.assertIsNone(out)

    def test_update_relationship_by_id_success(self):
        mock_rel = MagicMock()
        mock_rel.get.side_effect = lambda k: "myapp" if k == "app_id" else None
        mock_cursor = MagicMock()
        mock_cursor.single.return_value = {"r": mock_rel}
        self.mock_driver.run.return_value = mock_cursor

        out = relationship_repo.update_relationship_by_id("myapp", 1, {"weight": 2})
        self.assertIs(mock_rel, out)
        self.mock_driver.update_edge.assert_called_once()

    def test_query_relationships_returns_results_and_total(self):
        count_cursor = MagicMock()
        count_cursor.single.return_value = {"total": 1}
        rel_mock = MagicMock()
        rel_mock.identity = 10
        rel_mock.__iter__ = lambda self: iter([("app_id", "myapp"), ("x", 1)])
        a_mock = MagicMock()
        a_mock.get.side_effect = lambda k: 5 if k == "knowledge_id" else None
        b_mock = MagicMock()
        b_mock.get.side_effect = lambda k: ("user" if k == "entity_type" else ("e1" if k == "entity_id" else None))
        data_cursor = MagicMock()
        data_cursor.__iter__ = lambda self: iter([
            {"a": a_mock, "r": rel_mock, "b": b_mock, "end_labels": ["Entity"]}
        ])
        self.mock_driver.run.side_effect = [count_cursor, data_cursor]

        inp = RelationshipQueryInput(app_id="myapp", limit=10, offset=0)
        items, total = relationship_repo.query_relationships(inp)
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].relationship_type, "knowledge_entity")
        self.assertEqual(items[0].source_knowledge_id, 5)
        self.assertEqual(items[0].entity_type, "user")
        self.assertEqual(items[0].entity_id, "e1")

    def test_create_relationship_unknown_type_raises(self):
        inp = RelationshipCreateInput(
            app_id="myapp",
            relationship_type="unknown",
            source_knowledge_id=1,
        )
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.create_relationship(inp)
        self.assertIn("relationship_type", str(ctx.exception).lower())

    def test_get_relationship_by_id_zero_returns_none(self):
        out = relationship_repo.get_relationship_by_id("myapp", 0)
        self.assertIsNone(out)

    def test_get_relationship_by_id_negative_returns_none(self):
        out = relationship_repo.get_relationship_by_id("myapp", -1)
        self.assertIsNone(out)

    def test_get_relationship_by_id_empty_app_id_returns_none(self):
        out = relationship_repo.get_relationship_by_id("", 1)
        self.assertIsNone(out)

    def test_update_relationship_by_id_zero_returns_none(self):
        out = relationship_repo.update_relationship_by_id("myapp", 0, {"k": "v"})
        self.assertIsNone(out)

    def test_update_relationship_by_id_negative_returns_none(self):
        out = relationship_repo.update_relationship_by_id("myapp", -1, {"k": "v"})
        self.assertIsNone(out)

    def test_create_relationship_empty_app_id_raises(self):
        inp = RelationshipCreateInput(
            app_id="",
            relationship_type="knowledge_entity",
            source_knowledge_id=1,
            entity_type="user",
            entity_id="e1",
        )
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.create_relationship(inp)
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_query_relationships_empty_app_id_raises(self):
        inp = RelationshipQueryInput(app_id="", limit=10, offset=0)
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.query_relationships(inp)
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_update_relationship_by_id_non_dict_properties_raises(self):
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.update_relationship_by_id("myapp", 1, None)
        self.assertIn("properties", str(ctx.exception).lower())

    def test_get_related_by_knowledge_ids_empty_app_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.get_related_by_knowledge_ids([1, 2], "", limit=10)
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_get_related_by_knowledge_ids_empty_ids_returns_empty(self):
        out = relationship_repo.get_related_by_knowledge_ids([], "myapp", limit=10)
        self.assertEqual(out, [])
        out = relationship_repo.get_related_by_knowledge_ids([0, -1], "myapp", limit=10)
        self.assertEqual(out, [])

    def test_get_related_by_knowledge_ids_invalid_ids_raises(self):
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.get_related_by_knowledge_ids("not a list", "myapp", limit=10)
        self.assertIn("list", str(ctx.exception).lower())

    def test_get_related_by_knowledge_ids_invalid_limit_raises(self):
        with self.assertRaises(ValueError) as ctx:
            relationship_repo.get_related_by_knowledge_ids([1], "myapp", limit=0)
        self.assertIn("limit", str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            relationship_repo.get_related_by_knowledge_ids([1], "myapp", limit=-1)
        with self.assertRaises(ValueError):
            relationship_repo.get_related_by_knowledge_ids(
                [1], "myapp", limit=relationship_repo.REL_LIST_LIMIT + 1
            )
        with self.assertRaises(ValueError) as ctx2:
            relationship_repo.get_related_by_knowledge_ids([1], "myapp", limit="10")
        self.assertIn("integer", str(ctx2.exception).lower())

    def test_get_related_by_knowledge_ids_returns_knowledge_and_entity(self):
        b_know = MagicMock()
        b_know.get.side_effect = lambda k: 2 if k == "knowledge_id" else None
        b_ent = MagicMock()
        b_ent.get.side_effect = lambda k: ("user" if k == "entity_type" else ("e1" if k == "entity_id" else None))
        data_cursor = MagicMock()
        data_cursor.__iter__ = lambda self: iter([
            {"source_id": 1, "b": b_know, "end_labels": ["Knowledge"], "hop": 1, "predicates": ["related_to"]},
            {"source_id": 1, "b": b_ent, "end_labels": ["Entity"], "hop": 1, "predicates": ["belongs_to"]},
        ])
        self.mock_driver.run.return_value = data_cursor

        out = relationship_repo.get_related_by_knowledge_ids([1], "myapp", limit=20)
        self.assertEqual(len(out), 2)
        types = {r["type"] for r in out}
        self.assertEqual(types, {"knowledge", "entity"})
        knowledge_items = [r for r in out if r["type"] == "knowledge"]
        entity_items = [r for r in out if r["type"] == "entity"]
        self.assertEqual(knowledge_items[0]["knowledge_id"], 2)
        self.assertEqual(knowledge_items[0]["hop"], 1)
        self.assertEqual(knowledge_items[0]["predicate"], "related_to")
        self.assertEqual(entity_items[0]["entity_type"], "user")
        self.assertEqual(entity_items[0]["entity_id"], "e1")
        self.assertEqual(entity_items[0]["hop"], 1)
        self.assertEqual(entity_items[0]["predicate"], "belongs_to")
