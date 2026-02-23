"""
Tests for KnowledgeSummaryMapping repository CRUD operations. Generated.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.repos.summary_mapping_repo import (
    get_mapping_by_knowledge_id,
    get_mapping_by_summary_id,
    list_mappings,
    create_or_update_mapping,
    delete_mapping_by_knowledge_id,
    get_knowledge_ids_by_summary_ids,
)


class GetMappingByKnowledgeIdTest(TestCase):
    """Tests for get_mapping_by_knowledge_id."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_get_success(self, mock_model):
        mock_qs = MagicMock()
        mock_mapping = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.first.return_value = mock_mapping
        mock_model.objects.using.return_value = mock_qs

        result = get_mapping_by_knowledge_id(knowledge_id=1, app_id=1)
        self.assertEqual(result, mock_mapping)
        mock_qs.filter.assert_any_call(kid=1)

    def test_invalid_knowledge_id_returns_none(self):
        self.assertIsNone(get_mapping_by_knowledge_id(knowledge_id=0))
        self.assertIsNone(get_mapping_by_knowledge_id(knowledge_id=-1))
        self.assertIsNone(get_mapping_by_knowledge_id(knowledge_id=None))

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_exception_returns_none(self, mock_model):
        mock_model.objects.using.side_effect = RuntimeError("DB error")
        result = get_mapping_by_knowledge_id(knowledge_id=1)
        self.assertIsNone(result)


class GetMappingBySummaryIdTest(TestCase):
    """Tests for get_mapping_by_summary_id."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_get_success(self, mock_model):
        mock_qs = MagicMock()
        mock_mapping = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.first.return_value = mock_mapping
        mock_model.objects.using.return_value = mock_qs

        result = get_mapping_by_summary_id(summary_id="abc123", app_id=1)
        self.assertEqual(result, mock_mapping)

    def test_invalid_summary_id_returns_none(self):
        self.assertIsNone(get_mapping_by_summary_id(summary_id=""))
        self.assertIsNone(get_mapping_by_summary_id(summary_id=None))
        self.assertIsNone(get_mapping_by_summary_id(summary_id="   "))


class ListMappingsTest(TestCase):
    """Tests for list_mappings."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_list_success(self, mock_model):
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.count.return_value = 2
        mock_qs.__getitem__ = MagicMock(return_value=[MagicMock(), MagicMock()])
        mock_model.objects.using.return_value = mock_qs

        items, total = list_mappings(app_id=1, offset=0, limit=10)
        self.assertEqual(total, 2)
        self.assertEqual(len(items), 2)

    def test_invalid_offset_raises(self):
        with self.assertRaises(ValueError) as ctx:
            list_mappings(offset=-1, limit=10)
        self.assertIn("offset", str(ctx.exception))

    def test_invalid_limit_raises(self):
        with self.assertRaises(ValueError):
            list_mappings(offset=0, limit=0)
        with self.assertRaises(ValueError):
            list_mappings(offset=0, limit=LIMIT_LIST + 1)


class CreateOrUpdateMappingTest(TestCase):
    """Tests for create_or_update_mapping."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_create_new_mapping(self, mock_model):
        mock_mapping = MagicMock()
        mock_model.objects.using.return_value.get_or_create.return_value = (mock_mapping, True)

        result = create_or_update_mapping(knowledge_id=1, summary_id="abc123", app_id=1)
        self.assertEqual(result, mock_mapping)
        mock_model.objects.using.return_value.get_or_create.assert_called_once()

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_update_existing_mapping(self, mock_model):
        mock_mapping = MagicMock()
        mock_model.objects.using.return_value.get_or_create.return_value = (mock_mapping, False)

        result = create_or_update_mapping(knowledge_id=1, summary_id="new_id", app_id=1)
        self.assertEqual(result, mock_mapping)
        self.assertEqual(mock_mapping.sid, "new_id")
        mock_mapping.save.assert_called_once()

    def test_invalid_knowledge_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_or_update_mapping(knowledge_id=0, summary_id="abc", app_id=1)
        self.assertIn("knowledge_id", str(ctx.exception))

    def test_invalid_summary_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_or_update_mapping(knowledge_id=1, summary_id="", app_id=1)
        self.assertIn("summary_id", str(ctx.exception))

    def test_invalid_app_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_or_update_mapping(knowledge_id=1, summary_id="abc", app_id="")
        self.assertIn("app_id", str(ctx.exception))


class DeleteMappingByKnowledgeIdTest(TestCase):
    """Tests for delete_mapping_by_knowledge_id."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_delete_success(self, mock_model):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.delete.return_value = (2, {})
        mock_model.objects.using.return_value = mock_qs

        result = delete_mapping_by_knowledge_id(knowledge_id=1, app_id=1)
        self.assertEqual(result, 2)

    def test_invalid_knowledge_id_returns_zero(self):
        self.assertEqual(delete_mapping_by_knowledge_id(knowledge_id=0), 0)
        self.assertEqual(delete_mapping_by_knowledge_id(knowledge_id=-1), 0)
        self.assertEqual(delete_mapping_by_knowledge_id(knowledge_id=None), 0)


class GetKnowledgeIdsBySummaryIdsTest(TestCase):
    """Tests for get_knowledge_ids_by_summary_ids."""

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_get_success(self, mock_model):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.values_list.return_value = [1, 2, 3]
        mock_model.objects.using.return_value = mock_qs

        result = get_knowledge_ids_by_summary_ids(summary_ids=["a", "b", "c"], app_id=1)
        self.assertEqual(result, [1, 2, 3])

    def test_empty_summary_ids_returns_empty(self):
        self.assertEqual(get_knowledge_ids_by_summary_ids(summary_ids=[]), [])
        self.assertEqual(get_knowledge_ids_by_summary_ids(summary_ids=None), [])

    def test_whitespace_summary_ids_returns_empty(self):
        self.assertEqual(get_knowledge_ids_by_summary_ids(summary_ids=["", "  "]), [])

    @patch("app_know.repos.summary_mapping_repo.KnowledgeSummaryMapping")
    def test_exception_returns_empty(self, mock_model):
        mock_model.objects.using.side_effect = RuntimeError("DB error")
        result = get_knowledge_ids_by_summary_ids(summary_ids=["a"])
        self.assertEqual(result, [])
