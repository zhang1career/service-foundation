"""load_branch_metas_for_begin validation without DB round-trips for empty/duplicate."""

from django.test import SimpleTestCase

from app_tcc.services.biz_branch_service import (
    load_branch_metas_for_begin,
    load_branch_metas_for_begin_by_biz,
)


class LoadBranchMetasValidationTests(SimpleTestCase):
    def test_empty_ids_raises(self):
        with self.assertRaises(ValueError) as ctx:
            load_branch_metas_for_begin([])
        self.assertIn("required", str(ctx.exception).lower())

    def test_duplicate_ids_raises_before_query(self):
        with self.assertRaises(ValueError) as ctx:
            load_branch_metas_for_begin([10, 10])
        self.assertIn("duplicate", str(ctx.exception).lower())


class LoadBranchMetasByBizValidationTests(SimpleTestCase):
    def test_empty_branch_indices_raises(self):
        with self.assertRaises(ValueError) as ctx:
            load_branch_metas_for_begin_by_biz(1, [])
        self.assertIn("required", str(ctx.exception).lower())

    def test_duplicate_branch_indices_raises_before_query(self):
        with self.assertRaises(ValueError) as ctx:
            load_branch_metas_for_begin_by_biz(1, [0, 0])
        self.assertIn("duplicate", str(ctx.exception).lower())
