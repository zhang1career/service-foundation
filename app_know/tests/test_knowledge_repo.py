"""
Tests for knowledge_entity_compat repo (CRUD facade over Batch + KnowledgePoint).
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock

from app_know.repos import (
    get_knowledge_by_id,
    list_knowledge,
    create_knowledge,
    update_knowledge,
    delete_knowledge,
)
from common.consts.query_const import LIMIT_LIST
from common.utils.date_util import get_now_timestamp_ms

_COMPAT = "app_know.repos.knowledge_entity_compat"


class KnowledgeRepoTest(TestCase):
    """Tests for compat repo functions (fully mocked, no DB required)."""

    @patch(f"{_COMPAT}.create_knowledge_point")
    @patch(f"{_COMPAT}.create_batch")
    def test_create_and_get(self, mock_batch_model, mock_create_point):
        mock_batch = MagicMock()
        mock_batch.id = 1
        mock_batch_model.return_value = mock_batch
        mock_point = MagicMock()
        mock_point.id = 10
        mock_create_point.return_value = mock_point

        with patch(f"{_COMPAT}.get_batch_as_entity") as mock_as_entity:
            mock_as_entity.return_value = {
                "id": 1,
                "title": "Test Title",
                "description": "",
                "content": "Test content body",
                "source_type": "batch",
                "ct": 0,
                "ut": 0,
            }
            entity = create_knowledge(
                title="Test Title",
                description="Desc",
                content="Test content body",
                source_type="document",
                ct=0,
                ut=0,
            )
        self.assertEqual(entity.id, 1)
        self.assertEqual(entity.title, "Test Title")
        mock_batch_model.assert_called_once()
        mock_create_point.assert_called_once()

    @patch(f"{_COMPAT}.get_batch_as_entity")
    def test_get_knowledge_by_id_success(self, mock_as_entity):
        mock_as_entity.return_value = {
            "id": 1,
            "title": "Test Title",
            "description": "",
            "content": "x",
            "source_type": "batch",
            "ct": 0,
            "ut": 0,
        }
        got = get_knowledge_by_id(1)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Test Title")
        mock_as_entity.assert_called_once_with(1)

    @patch(f"{_COMPAT}.get_batch_as_entity")
    def test_get_not_found(self, mock_as_entity):
        mock_as_entity.return_value = None
        self.assertIsNone(get_knowledge_by_id(99999))

    @patch(f"{_COMPAT}.Batch")
    def test_list_knowledge(self, mock_batch_model):
        mock_b = MagicMock()
        mock_b.id = 1
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 3
        def _getitem(_self, s):
            rows = [mock_b, mock_b, mock_b]
            return rows[s] if isinstance(s, int) else rows[s]

        mock_qs.__getitem__ = _getitem
        mock_batch_model.objects.using.return_value = mock_qs

        with patch(f"{_COMPAT}.get_batch_as_entity") as mock_as_entity:
            mock_as_entity.side_effect = lambda bid: {
                "id": bid,
                "title": f"T{bid}",
                "description": "",
                "content": "",
                "source_type": "batch",
                "ct": 0,
                "ut": 0,
            }
            items, total = list_knowledge(offset=0, limit=10)
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 3)

    @patch(f"{_COMPAT}.Batch")
    def test_list_knowledge_with_source_type_filter(self, mock_batch_model):
        mock_b = MagicMock()
        mock_b.id = 3
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.count.return_value = 1
        def _getitem(_self, s):
            rows = [mock_b]
            return rows[s] if isinstance(s, int) else rows[s]

        mock_qs.__getitem__ = _getitem
        mock_batch_model.objects.using.return_value = mock_qs

        with patch(f"{_COMPAT}.get_batch_as_entity") as mock_as_entity:
            mock_as_entity.return_value = {
                "id": 3,
                "title": "C",
                "description": "",
                "content": "",
                "source_type": "batch",
                "ct": 0,
                "ut": 0,
            }
            items, total = list_knowledge(offset=0, limit=10, source_type="url")
        self.assertEqual(total, 1)
        mock_qs.filter.assert_called()

    @patch(f"{_COMPAT}.update_content")
    @patch(f"{_COMPAT}.list_by_batch")
    @patch(f"{_COMPAT}.update_knowledge_point")
    def test_update_knowledge(self, mock_update_point, mock_list_batch, mock_upd_content):
        mock_point = MagicMock()
        mock_point.id = 5
        mock_point.seq = 0
        mock_list_batch.return_value = ([mock_point], 1)
        mock_update_point.return_value = True

        mock_entity = MagicMock()
        mock_entity.id = 1
        mock_entity.title = "Old"
        mock_entity.description = ""
        mock_entity.content = ""

        n = update_knowledge(mock_entity, title="Updated", ut=get_now_timestamp_ms())
        self.assertEqual(n, 1)
        mock_update_point.assert_called_once()

    @patch(f"{_COMPAT}.delete_batch")
    @patch(f"{_COMPAT}.delete_by_batch")
    def test_delete_knowledge(self, mock_del_points, mock_del_batch):
        mock_del_points.return_value = 2
        mock_del_batch.return_value = True

        ok = delete_knowledge(1)
        self.assertTrue(ok)
        mock_del_points.assert_called_once_with(1)
        mock_del_batch.assert_called_once_with(1)

    @patch(f"{_COMPAT}.delete_by_batch")
    @patch(f"{_COMPAT}.delete_batch")
    def test_delete_knowledge_not_found(self, mock_del_batch, mock_del_points):
        mock_del_points.return_value = 0
        mock_del_batch.return_value = False

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
            create_knowledge(
                title="",
                description=None,
                content=None,
                source_type="doc",
                ct=0,
                ut=0,
            )
        self.assertIn("title", str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            create_knowledge(
                title="   ",
                description=None,
                content=None,
                source_type="doc",
                ct=0,
                ut=0,
            )

    def test_update_none_entity_raises(self):
        with self.assertRaises(ValueError) as ctx:
            update_knowledge(None, title="x")
        self.assertIn("entity", str(ctx.exception).lower())

    def test_delete_invalid_entity_id_returns_false(self):
        self.assertFalse(delete_knowledge(None))
        self.assertFalse(delete_knowledge(-1))
        self.assertFalse(delete_knowledge(0))
