"""
Tests for knowledge service (validation and CRUD).
Generated.
"""
import time as time_module
from django.db import transaction, connections
from django.test import TestCase

from common.consts.query_const import LIMIT_LIST

from app_know.models import Knowledge
from app_know.services.knowledge_service import (
    KnowledgeService,
    TITLE_MAX_LEN,
    SOURCE_TYPE_MAX_LEN,
)


class KnowledgeServiceTest(TestCase):
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

    def test_create_requires_title(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.create_knowledge(title="")
        self.assertIn("required", str(ctx.exception).lower())

    def test_create_success(self):
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

    def test_get_not_found(self):
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

    def test_update_not_found(self):
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(99999, title="X")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_delete_not_found(self):
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

    def test_update_title_too_long_raises(self):
        entity = Knowledge.objects.using("know_rw").create(
            title="Original",
            source_type="doc",
            ct=int(time_module.time() * 1000),
            ut=int(time_module.time() * 1000),
        )
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(entity.id, title="x" * (TITLE_MAX_LEN + 1))
        self.assertIn("title", str(ctx.exception).lower())

    def test_update_source_type_too_long_raises(self):
        entity = Knowledge.objects.using("know_rw").create(
            title="Original",
            source_type="doc",
            ct=int(time_module.time() * 1000),
            ut=int(time_module.time() * 1000),
        )
        svc = KnowledgeService()
        with self.assertRaises(ValueError) as ctx:
            svc.update_knowledge(entity.id, source_type="x" * (SOURCE_TYPE_MAX_LEN + 1))
        self.assertIn("source_type", str(ctx.exception).lower())
