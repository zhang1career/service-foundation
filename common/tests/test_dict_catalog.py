"""Tests for dict code registry and get_dict_by_codes."""
import uuid

from django.test import SimpleTestCase

from common.dict_catalog import get_dict_by_codes, register_dict_code


class DictCatalogTest(SimpleTestCase):
    def test_dynamic_register_and_query(self):
        code = f"dict_catalog_tmp_{uuid.uuid4().hex[:10]}"

        class _Tmp:
            @classmethod
            def to_dict_list(cls):
                return [{"k": "t", "v": "9"}]

        register_dict_code(code)(_Tmp)
        self.assertEqual(
            get_dict_by_codes(f"{code},unknown_xyz"),
            {code: [{"k": "t", "v": "9"}]},
        )
