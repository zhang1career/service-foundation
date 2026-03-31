"""NestedParamType dict registration (bundled catalog)."""
from django.test import SimpleTestCase

from common.dict_catalog import get_dict_by_codes


class NestedParamTypeDictTest(SimpleTestCase):
    def test_dict_code_registered(self):
        out = get_dict_by_codes("aibroker_nested_param_type")
        items = out.get("aibroker_nested_param_type")
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        vs = {str(x["v"]) for x in items if isinstance(x, dict)}
        self.assertIn("STRING", vs)
        self.assertIn("OBJECT_ARRAY", vs)
