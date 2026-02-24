"""
Tests for knowledge repository (CRUD on know_rw).
Generated.
"""
import time
from unittest.mock import patch, MagicMock

from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.repos import (
    get_knowledge_by_id,
    list_knowledge,
    create_knowledge,
    update_knowledge,
    delete_knowledge,
)


class KnowledgeRepoTest(TestCase):
    """Tests for knowledge repo functions (fully mocked, no DB required)."""

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_create_and_get(self, mock_model):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_entity.title = "Test Title"
        mock_entity.source_type = "document"
        mock_model.objects.using.return_value.create.return_value = mock_entity

        entity = create_knowledge(
            title="Test Title",
            description="Desc",
            content="Test content body",
            source_type="document",
        )
        self.assertIsNotNone(entity.id)
        self.assertEqual(entity.title, "Test Title")
        self.assertEqual(entity.source_type, "document")
        mock_model.objects.using.assert_called_with("know_rw")

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_get_knowledge_by_id_success(self, mock_model):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_entity.title = "Test Title"
        mock_qs = MagicMock()
        mock_qs.filter.return_value.first.return_value = mock_entity
        mock_model.objects.using.return_value = mock_qs

        got = get_knowledge_by_id(1)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Test Title")
        mock_qs.filter.assert_called_once_with(id=1)

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_get_not_found(self, mock_model):
        mock_qs = MagicMock()
        mock_qs.filter.return_value.first.return_value = None
        mock_model.objects.using.return_value = mock_qs

        self.assertIsNone(get_knowledge_by_id(99999))

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_list_knowledge(self, mock_model):
        mock_item1 = MagicMock(id=1, title="A")
        mock_item2 = MagicMock(id=2, title="B")
        mock_item3 = MagicMock(id=3, title="C")
        mock_items = [mock_item1, mock_item2, mock_item3]

        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 3
        mock_qs.__getitem__ = lambda self, s: mock_items[s] if isinstance(s, int) else mock_items
        mock_model.objects.using.return_value = mock_qs

        items, total = list_knowledge(offset=0, limit=10)
        self.assertEqual(total, 3)

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_list_knowledge_with_source_type_filter(self, mock_model):
        mock_item = MagicMock(id=3, title="C")
        mock_items = [mock_item]

        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 1
        mock_qs.__getitem__ = lambda self, s: mock_items[s] if isinstance(s, int) else mock_items
        mock_model.objects.using.return_value = mock_qs

        items, total = list_knowledge(offset=0, limit=10, source_type="url")
        self.assertEqual(total, 1)
        mock_qs.filter.assert_called()

    @patch("app_know.repos.knowledge_repo.Knowledge")
    def test_update_knowledge(self, mock_model):
        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_qs = MagicMock()
        mock_qs.filter.return_value.update.return_value = 1
        mock_model.objects.using.return_value = mock_qs

        n = update_knowledge(mock_entity, title="Updated", ut=int(time.time() * 1000))
        self.assertEqual(n, 1)

    @patch("app_know.repos.knowledge_repo.get_knowledge_by_id")
    def test_delete_knowledge(self, mock_get):
        mock_entity = MagicMock()
        mock_entity.delete = MagicMock()
        mock_get.return_value = mock_entity

        ok = delete_knowledge(1)
        self.assertTrue(ok)
        mock_entity.delete.assert_called_once()

    @patch("app_know.repos.knowledge_repo.get_knowledge_by_id")
    def test_delete_knowledge_not_found(self, mock_get):
        mock_get.return_value = None

        ok = delete_knowledge(99999)
        self.assertFalse(ok)

    def test_get_invalid_entity_id_returns_none(self):
        self.assertIsNone(get_knowledge_by_id(None))
        self.assertIsNone(get_knowledge_by_id(-1))
        self.assertIsNone(get_knowledge_by_id(0))
        self.assertIsNone(get_knowledge_by_id("1"))

    def test_list_validation_invalid_offset(self):
        with self.assertRaises(ValueError) as ctx:
            list_knowledge(offset=-1, limit=10)
        self.assertIn("offset", str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            list_knowledge(offset=None, limit=10)

    def test_list_validation_invalid_limit(self):
        with self.assertRaises(ValueError) as ctx:
            list_knowledge(offset=0, limit=0)
        self.assertIn("limit", str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            list_knowledge(offset=0, limit=LIMIT_LIST + 1)
        with self.assertRaises(ValueError):
            list_knowledge(offset=0, limit=None)

    def test_create_empty_title_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_knowledge(title="", source_type="doc")
        self.assertIn("title", str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            create_knowledge(title="   ", source_type="doc")

    def test_update_none_entity_raises(self):
        with self.assertRaises(ValueError) as ctx:
            update_knowledge(None, title="x")
        self.assertIn("entity", str(ctx.exception).lower())

    def test_delete_invalid_entity_id_returns_false(self):
        self.assertFalse(delete_knowledge(None))
        self.assertFalse(delete_knowledge(-1))
        self.assertFalse(delete_knowledge(0))
