"""
Tests for knowledge repository (CRUD on know_rw).
Generated.
"""
import time
from django.db import transaction, connections
from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.models import Knowledge
from app_know.repos import (
    get_knowledge_by_id,
    list_knowledge,
    create_knowledge,
    update_knowledge,
    delete_knowledge,
)


class KnowledgeRepoTest(TestCase):
    databases = {"default", "know_rw"}

    def setUp(self):
        Knowledge.objects.using("know_rw").all().delete()

    def tearDown(self):
        try:
            Knowledge.objects.using("know_rw").all().delete()
        except Exception:
            conn = connections["know_rw"]
            if conn.in_atomic_block:
                transaction.set_rollback(True, using="know_rw")

    def test_create_and_get(self):
        entity = create_knowledge(
            title="Test Title",
            description="Desc",
            source_type="document",
            metadata='{"k": "v"}',
        )
        self.assertIsNotNone(entity.id)
        self.assertEqual(entity.title, "Test Title")
        self.assertEqual(entity.source_type, "document")
        got = get_knowledge_by_id(entity.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Test Title")

    def test_get_not_found(self):
        self.assertIsNone(get_knowledge_by_id(99999))

    def test_list_knowledge(self):
        create_knowledge(title="A", source_type="doc")
        create_knowledge(title="B", source_type="doc")
        create_knowledge(title="C", source_type="url")
        items, total = list_knowledge(offset=0, limit=10)
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 3)
        items2, total2 = list_knowledge(offset=0, limit=2)
        self.assertEqual(total2, 3)
        self.assertEqual(len(items2), 2)
        items3, total3 = list_knowledge(offset=0, limit=10, source_type="url")
        self.assertEqual(total3, 1)
        self.assertEqual(items3[0].title, "C")

    def test_update_knowledge(self):
        entity = create_knowledge(title="Original", source_type="doc")
        n = update_knowledge(entity, title="Updated", ut=int(time.time() * 1000))
        self.assertEqual(n, 1)
        got = get_knowledge_by_id(entity.id)
        self.assertEqual(got.title, "Updated")

    def test_delete_knowledge(self):
        entity = create_knowledge(title="To Delete", source_type="doc")
        ok = delete_knowledge(entity.id)
        self.assertTrue(ok)
        self.assertIsNone(get_knowledge_by_id(entity.id))
        ok2 = delete_knowledge(entity.id)
        self.assertFalse(ok2)

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
