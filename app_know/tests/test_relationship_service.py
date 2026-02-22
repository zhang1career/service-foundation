"""
Tests for relationship service (validation, create/update/query, and edge cases).
Generated.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.models.relationships import RelationshipQueryResult
from app_know.services.relationship_service import (
    RelationshipService,
    APP_ID_MAX_LEN,
    ENTITY_TYPE_MAX_LEN,
    ENTITY_ID_MAX_LEN,
)


class RelationshipServiceTest(TestCase):
    def test_create_requires_app_id(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="",
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
                entity_type="user",
                entity_id="e1",
            )
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_create_requires_relationship_type(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="invalid_type",
                source_knowledge_id=1,
                entity_type="user",
                entity_id="e1",
            )
        self.assertIn("relationship_type", str(ctx.exception).lower())

    def test_create_knowledge_entity_requires_entity_type_and_id(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
            )
        self.assertIn("entity_type", str(ctx.exception).lower())
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
                entity_type="user",
            )
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_create_knowledge_knowledge_requires_target_knowledge_id(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_knowledge",
                source_knowledge_id=1,
            )
        self.assertIn("target_knowledge_id", str(ctx.exception).lower())

    @patch("app_know.services.relationship_service.repo_create")
    def test_create_knowledge_entity_success(self, mock_create):
        class RelMock:
            identity = 100

            def __iter__(self):
                return iter([("app_id", "myapp"), ("weight", 1)])

        mock_create.return_value = (RelMock(), MagicMock(), MagicMock())
        svc = RelationshipService()
        out = svc.create_relationship(
            app_id="myapp",
            relationship_type="knowledge_entity",
            source_knowledge_id=1,
            entity_type="user",
            entity_id="e1",
            properties={"weight": 1},
        )
        self.assertIn("relationship_id", out)
        self.assertEqual(out["app_id"], "myapp")
        self.assertEqual(out["relationship_type"], "knowledge_entity")
        self.assertEqual(out["source_knowledge_id"], 1)
        self.assertEqual(out["entity_type"], "user")
        self.assertEqual(out["entity_id"], "e1")
        mock_create.assert_called_once()

    @patch("app_know.services.relationship_service.repo_create")
    def test_create_knowledge_knowledge_success(self, mock_create):
        class RelMock:
            identity = 101

            def __iter__(self):
                return iter([("app_id", "myapp")])

        mock_create.return_value = (RelMock(), MagicMock(), MagicMock())
        svc = RelationshipService()
        out = svc.create_relationship(
            app_id="myapp",
            relationship_type="knowledge_knowledge",
            source_knowledge_id=1,
            target_knowledge_id=2,
        )
        self.assertEqual(out["relationship_type"], "knowledge_knowledge")
        self.assertEqual(out["source_knowledge_id"], 1)
        self.assertEqual(out["target_knowledge_id"], 2)

    def test_create_invalid_source_knowledge_id_raises(self):
        svc = RelationshipService()
        for invalid in (None, -1, 0, "x"):
            with self.assertRaises(ValueError):
                svc.create_relationship(
                    app_id="myapp",
                    relationship_type="knowledge_entity",
                    source_knowledge_id=invalid,
                    entity_type="user",
                    entity_id="e1",
                )

    def test_update_requires_app_id(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_relationship(
                app_id="",
                relationship_id=1,
                properties={"k": "v"},
            )
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_update_requires_properties_dict(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_relationship(
                app_id="myapp",
                relationship_id=1,
                properties=None,
            )
        self.assertIn("properties", str(ctx.exception).lower())

    @patch("app_know.services.relationship_service.update_relationship_by_id")
    def test_update_not_found_raises(self, mock_update):
        mock_update.return_value = None
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_relationship(
                app_id="myapp",
                relationship_id=999,
                properties={"k": "v"},
            )
        self.assertIn("not found", str(ctx.exception).lower())

    @patch("app_know.services.relationship_service.update_relationship_by_id")
    def test_update_success(self, mock_update):
        class RelMock:
            identity = 1

            def __iter__(self):
                return iter([("app_id", "myapp"), ("k", "v")])

        mock_update.return_value = RelMock()
        svc = RelationshipService()
        out = svc.update_relationship(
            app_id="myapp",
            relationship_id=1,
            properties={"k": "v"},
        )
        self.assertEqual(out["relationship_id"], 1)
        self.assertEqual(out["app_id"], "myapp")
        self.assertEqual(out["properties"], {"k": "v"})

    def test_query_requires_app_id(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.query_relationships(app_id="")
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_query_validation_offset_negative(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.query_relationships(app_id="myapp", offset=-1)
        self.assertIn("offset", str(ctx.exception).lower())

    def test_query_validation_limit_invalid(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError):
            svc.query_relationships(app_id="myapp", limit=0)
        with self.assertRaises(ValueError):
            svc.query_relationships(app_id="myapp", limit=LIMIT_LIST + 1)

    @patch("app_know.services.relationship_service.repo_query")
    def test_query_success(self, mock_query):
        mock_query.return_value = (
            [
                RelationshipQueryResult(
                    relationship_id=1,
                    app_id="myapp",
                    relationship_type="knowledge_entity",
                    source_knowledge_id=10,
                    entity_type="user",
                    entity_id="e1",
                    properties={},
                )
            ],
            1,
        )
        svc = RelationshipService()
        out = svc.query_relationships(app_id="myapp", limit=10, offset=0)
        self.assertEqual(out["total_num"], 1)
        self.assertEqual(len(out["data"]), 1)
        self.assertEqual(out["data"][0]["source_knowledge_id"], 10)
        self.assertEqual(out["data"][0]["entity_type"], "user")

    def test_app_id_too_long_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="x" * (APP_ID_MAX_LEN + 1),
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
                entity_type="user",
                entity_id="e1",
            )
        self.assertIn("app_id", str(ctx.exception).lower())

    def test_entity_type_too_long_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
                entity_type="x" * (ENTITY_TYPE_MAX_LEN + 1),
                entity_id="e1",
            )
        self.assertIn("entity_type", str(ctx.exception).lower())

    def test_entity_id_too_long_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=1,
                entity_type="user",
                entity_id="x" * (ENTITY_ID_MAX_LEN + 1),
            )
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_validate_positive_int_rejects_bool(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=True,
                entity_type="user",
                entity_id="e1",
            )
        self.assertIn("integer", str(ctx.exception).lower())

    def test_validate_positive_int_rejects_non_whole_float(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_relationship(
                app_id="myapp",
                relationship_type="knowledge_entity",
                source_knowledge_id=1.5,
                entity_type="user",
                entity_id="e1",
            )
        self.assertIn("integer", str(ctx.exception).lower())

    def test_update_empty_properties_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_relationship(
                app_id="myapp",
                relationship_id=1,
                properties={},
            )
        self.assertIn("properties", str(ctx.exception).lower())

    @patch("app_know.services.relationship_service.repo_query")
    def test_query_entity_type_entity_id_empty_string_normalized_to_none(self, mock_query):
        mock_query.return_value = ([], 0)
        svc = RelationshipService()
        svc.query_relationships(
            app_id="myapp",
            entity_type="   ",
            entity_id="",
            limit=10,
            offset=0,
        )
        call_args = mock_query.call_args[0][0]
        self.assertIsNone(call_args.entity_type)
        self.assertIsNone(call_args.entity_id)

    def test_query_entity_type_too_long_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.query_relationships(
                app_id="myapp",
                entity_type="x" * (ENTITY_TYPE_MAX_LEN + 1),
                limit=10,
                offset=0,
            )
        self.assertIn("entity_type", str(ctx.exception).lower())

    def test_query_entity_id_too_long_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError) as ctx:
            svc.query_relationships(
                app_id="myapp",
                entity_id="x" * (ENTITY_ID_MAX_LEN + 1),
                limit=10,
                offset=0,
            )
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_get_relationship_invalid_id_raises(self):
        svc = RelationshipService()
        with self.assertRaises(ValueError):
            svc.get_relationship(app_id="myapp", relationship_id=0)
        with self.assertRaises(ValueError):
            svc.get_relationship(app_id="myapp", relationship_id=-1)
        with self.assertRaises(ValueError):
            svc.get_relationship(app_id="myapp", relationship_id=1.5)
