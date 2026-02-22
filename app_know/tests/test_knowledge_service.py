"""
Tests for knowledge service (validation and CRUD).
Generated.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.services.knowledge_service import (
    KnowledgeService,
    TITLE_MAX_LEN,
    SOURCE_TYPE_MAX_LEN,
)


class KnowledgeServiceTest(TestCase):
    """Tests for KnowledgeService (fully mocked, no DB required)."""

    def test_create_requires_title(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_knowledge(title="")
        self.assertIn("required", str(ctx.exception).lower())

    @patch("app_know.services.knowledge_service.create_knowledge")
    def test_create_success(self, mock_create):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_entity.title = "My Title"
        mock_entity.description = "My desc"
        mock_entity.source_type = "document"
        mock_entity.metadata = None
        mock_entity.ct = 1700000000000
        mock_entity.ut = 1700000000000
        mock_create.return_value = mock_entity

        svc = KnowledgeService()
        out = svc.create_knowledge(
            title="My Title",
            description="My desc",
            source_type="document",
        )
        self.assertIn("id", out)
        self.assertEqual(out["title"], "My Title")
        self.assertEqual(out["description"], "My desc")
        self.assertEqual(out["source_type"], "document")
        self.assertIn("ct", out)
        self.assertIn("ut", out)
        mock_create.assert_called_once()

    @patch("app_know.services.knowledge_service.get_knowledge_by_id")
    def test_get_not_found(self, mock_get):
        mock_get.return_value = None
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.get_knowledge(99999)
        self.assertIn("not found", str(ctx.exception).lower())

    def test_list_validation(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError):
            svc.list_knowledge(offset=-1)
        with self.assertRaises(ValueError):
            svc.list_knowledge(limit=0)

    @patch("app_know.services.knowledge_service.get_knowledge_by_id")
    def test_update_not_found(self, mock_get):
        mock_get.return_value = None
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(99999, title="X")
        self.assertIn("not found", str(ctx.exception).lower())

    @patch("app_know.services.knowledge_service.delete_knowledge")
    def test_delete_not_found(self, mock_delete):
        mock_delete.return_value = False
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.delete_knowledge(99999)
        self.assertIn("not found", str(ctx.exception).lower())

    def test_get_invalid_entity_id_raises(self):
        svc = KnowledgeService()
        for invalid in (None, -1, 0):
            with self.assertRaises(ValueError) as ctx:
                svc.get_knowledge(invalid)
            self.assertIn("entity_id", str(ctx.exception).lower())

    def test_update_invalid_entity_id_raises(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(0, title="x")
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_delete_invalid_entity_id_raises(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.delete_knowledge(-1)
        self.assertIn("entity_id", str(ctx.exception).lower())

    def test_list_limit_over_max_raises(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.list_knowledge(offset=0, limit=LIMIT_LIST + 1)
        self.assertIn("limit", str(ctx.exception).lower())

    def test_create_title_too_long_raises(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_knowledge(title="x" * (TITLE_MAX_LEN + 1))
        self.assertIn("title", str(ctx.exception).lower())

    def test_create_source_type_too_long_raises(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_knowledge(title="Ok", source_type="x" * (SOURCE_TYPE_MAX_LEN + 1))
        self.assertIn("source_type", str(ctx.exception).lower())

    @patch("app_know.services.knowledge_service.get_knowledge_by_id")
    def test_update_title_too_long_raises(self, mock_get):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_get.return_value = mock_entity

        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(1, title="x" * (TITLE_MAX_LEN + 1))
        self.assertIn("title", str(ctx.exception).lower())

    @patch("app_know.services.knowledge_service.get_knowledge_by_id")
    def test_update_source_type_too_long_raises(self, mock_get):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_get.return_value = mock_entity

        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(1, source_type="x" * (SOURCE_TYPE_MAX_LEN + 1))
        self.assertIn("source_type", str(ctx.exception).lower())
