import json
from unittest import TestCase


class TestTryParseJsonList(TestCase):
    def test_blank_and_valid(self):
        from common.utils.nested_typed_tree_util import try_parse_json_list

        self.assertEqual(try_parse_json_list(None), ([], None))
        self.assertEqual(try_parse_json_list(""), ([], None))
        self.assertEqual(try_parse_json_list("  "), ([], None))
        self.assertEqual(try_parse_json_list("[]"), ([], None))
        data, err = try_parse_json_list('[{"a":1}]')
        self.assertIsNone(err)
        self.assertEqual(data, [{"a": 1}])

    def test_invalid_json_and_not_array(self):
        from common.utils.nested_typed_tree_util import try_parse_json_list

        _, err = try_parse_json_list("{")
        self.assertEqual(err, "must be valid JSON")
        _, err2 = try_parse_json_list("{}")
        self.assertEqual(err2, "root must be a JSON array")


class TestIterTypedTreeLeaves(TestCase):
    def _accessors(self):
        def get_local_name(n: dict):
            v = n.get("n")
            return v.strip() if isinstance(v, str) else None

        def get_type_tag(n: dict):
            v = n.get("t")
            return str(v).strip().upper() if v is not None else ""

        def get_child_list(n: dict):
            v = n.get("c")
            return v if isinstance(v, list) else []

        def norm(t: str) -> str:
            return (t or "").strip().upper() or "STRING"

        return get_local_name, get_type_tag, get_child_list, norm

    def test_flat_and_nested(self):
        from common.utils.nested_typed_tree_util import iter_typed_tree_leaves

        get_local_name, get_type_tag, get_child_list, norm = self._accessors()
        items = json.loads(
            '[{"n":"a","t":"INT","r":{}},'
            '{"n":"o","t":"OBJECT","r":{},'
            '"c":[{"n":"inner","t":"STRING","r":{}}]}]'
        )
        leaves = list(
            iter_typed_tree_leaves(
                items,
                get_local_name=get_local_name,
                get_type_tag=get_type_tag,
                get_child_list=get_child_list,
                normalize_type_tag=norm,
            )
        )
        self.assertEqual(len(leaves), 2)
        self.assertEqual(leaves[0][1], "a")
        self.assertEqual(leaves[1][1], "o.inner")

    def test_object_array_with_child_column_yields_dotted_leaf(self):
        from common.utils.nested_typed_tree_util import iter_typed_tree_leaves

        get_local_name, get_type_tag, get_child_list, norm = self._accessors()
        items = json.loads(
            '[{"n":"items","t":"OBJECT_ARRAY","r":{},'
            '"c":[{"n":"id","t":"INT","r":{}}]}]'
        )
        leaves = list(
            iter_typed_tree_leaves(
                items,
                get_local_name=get_local_name,
                get_type_tag=get_type_tag,
                get_child_list=get_child_list,
                normalize_type_tag=norm,
            )
        )
        self.assertEqual([x[1] for x in leaves], ["items.id"])


class TestWalkTypedTreePreorder(TestCase):
    def test_preorder_depth(self):
        from common.utils.nested_typed_tree_util import walk_typed_tree_preorder

        seen: list[tuple[str, int]] = []

        def get_local_name(n: dict):
            v = n.get("n")
            return v.strip() if isinstance(v, str) else None

        def get_type_tag(n: dict):
            return str(n.get("t", "")).strip().upper()

        def get_child_list(n: dict):
            v = n.get("c")
            return v if isinstance(v, list) else []

        def visit(node: dict, depth: int, typ: str, ch: list) -> None:
            n = get_local_name(node)
            if n:
                seen.append((n, depth))

        items = json.loads(
            '[{"n":"root","t":"OBJECT","r":{},'
            '"c":[{"n":"leaf","t":"STRING","r":{}}]}]'
        )
        walk_typed_tree_preorder(
            items,
            get_local_name=get_local_name,
            get_type_tag=get_type_tag,
            get_child_list=get_child_list,
            normalize_type_tag=lambda t: (t or "").strip().upper() or "STRING",
            visit=visit,
        )
        self.assertEqual(seen, [("root", 0), ("leaf", 1)])


def _wire_like_name(node: dict):
    v = node.get("n")
    return v.strip() if isinstance(v, str) else None


def _wire_like_type(node: dict) -> str:
    v = node.get("t")
    return str(v).strip().upper() if v is not None else ""


def _wire_like_children(node: dict) -> list:
    v = node.get("c")
    return v if isinstance(v, list) else []


def _allowed_demo_tags():
    from common.enums.nested_type_enum import NestedParamType

    return NestedParamType.all_tag_values()


class TestValidateTypedRecordTree(TestCase):
    def test_valid_nested(self):
        from common.utils.nested_typed_tree_util import (
            DEFAULT_BRANCH_TAGS,
            validate_typed_record_tree,
        )

        nodes = json.loads(
            '[{"n":"o","t":"OBJECT","r":{},'
            '"c":[{"n":"x","t":"STRING","r":{}}]}]'
        )
        err = validate_typed_record_tree(
            nodes,
            get_local_name=_wire_like_name,
            get_type_tag=_wire_like_type,
            get_child_list=_wire_like_children,
            allowed_type_tags=_allowed_demo_tags(),
            branch_tags=DEFAULT_BRANCH_TAGS,
        )
        self.assertIsNone(err)

    def test_string_with_children_rejected(self):
        from common.utils.nested_typed_tree_util import (
            DEFAULT_BRANCH_TAGS,
            validate_typed_record_tree,
        )

        nodes = json.loads(
            '[{"n":"bad","t":"STRING","r":{},'
            '"c":[{"n":"x","t":"INT","r":{}}]}]'
        )
        err = validate_typed_record_tree(
            nodes,
            get_local_name=_wire_like_name,
            get_type_tag=_wire_like_type,
            get_child_list=_wire_like_children,
            allowed_type_tags=_allowed_demo_tags(),
            branch_tags=DEFAULT_BRANCH_TAGS,
        )
        self.assertIn("non-branching", err or "")

    def test_unknown_type(self):
        from common.utils.nested_typed_tree_util import (
            DEFAULT_BRANCH_TAGS,
            validate_typed_record_tree,
        )

        nodes = [{"n": "x", "t": "not_a_type", "r": {}, "c": []}]
        err = validate_typed_record_tree(
            nodes,
            get_local_name=_wire_like_name,
            get_type_tag=_wire_like_type,
            get_child_list=_wire_like_children,
            allowed_type_tags=_allowed_demo_tags(),
            branch_tags=DEFAULT_BRANCH_TAGS,
        )
        self.assertIn("unknown type", err or "")


class TestApplyFieldCoercion(TestCase):
    def test_default_handlers_and_string_fallback(self):
        from common.utils.nested_typed_tree_util import apply_field_coercion

        coerced, err = apply_field_coercion(
            "n",
            "3",
            {"name": "n", "type": "INT", "range": {"min": 1, "max": 10}},
        )
        self.assertIsNone(err)
        self.assertEqual(coerced, 3)

        s, err2 = apply_field_coercion(
            "s",
            "ok",
            {"name": "s", "type": "STRING", "range": {}},
        )
        self.assertIsNone(err2)
        self.assertEqual(s, "ok")

        _, err3 = apply_field_coercion(
            "n",
            "x",
            {"name": "n", "type": "INT", "range": {}},
        )
        self.assertIsNotNone(err3)
        self.assertIn("invalid", err3 or "")


class TestCoerceToHelpers(TestCase):
    def test_bool_enum_array_object(self):
        from common.utils.nested_typed_tree_util import (
            coerce_to_bool,
            coerce_to_enum_choice,
            coerce_to_json_list,
            coerce_to_object_like,
            coerce_to_object_list,
        )

        self.assertEqual(coerce_to_bool("", "1", {}), (True, None))
        v, err = coerce_to_enum_choice("", "b", {"range": {"values": ["a", "b"]}})
        self.assertIsNone(err)
        self.assertEqual(v, "b")
        a, e2 = coerce_to_json_list("", "[1,2]", {"range": {}})
        self.assertIsNone(e2)
        self.assertEqual(a, [1, 2])
        o, e3 = coerce_to_object_like("", '{"x":1}', {"range": {}})
        self.assertIsNone(e3)
        self.assertEqual(o, {"x": 1})
        _, e4 = coerce_to_object_list("", "[1]", {"range": {}})
        self.assertIsNotNone(e4)


class TestWrapObjectArrayDictBranchesAsSingleElementLists(TestCase):
    def test_wraps_dict_assembled_from_dotted_paths(self):
        from common.utils.nested_typed_tree_util import (
            wrap_object_array_dict_branches_as_single_element_lists,
        )

        items = json.loads(
            '[{"n":"messages","t":"OBJECT_ARRAY","r":{},'
            '"c":['
            '{"n":"role","t":"STRING","r":{}},'
            '{"n":"text","t":"STRING","r":{}}'
            "]}]"
        )
        payload = {"messages": {"role": "user", "text": "hello"}}
        wrap_object_array_dict_branches_as_single_element_lists(
            items,
            payload,
            get_local_name=_wire_like_name,
            get_type_tag=_wire_like_type,
            get_child_list=_wire_like_children,
            normalize_type_tag=lambda t: (t or "").strip().upper() or "STRING",
        )
        self.assertEqual(payload["messages"], [{"role": "user", "text": "hello"}])

    def test_leaves_existing_list_unchanged(self):
        from common.utils.nested_typed_tree_util import (
            wrap_object_array_dict_branches_as_single_element_lists,
        )

        items = json.loads(
            '[{"n":"messages","t":"OBJECT_ARRAY","r":{},'
            '"c":[{"n":"role","t":"STRING","r":{}}]}]'
        )
        payload = {"messages": [{"role": "assistant"}]}
        wrap_object_array_dict_branches_as_single_element_lists(
            items,
            payload,
            get_local_name=_wire_like_name,
            get_type_tag=_wire_like_type,
            get_child_list=_wire_like_children,
            normalize_type_tag=lambda t: (t or "").strip().upper() or "STRING",
        )
        self.assertEqual(payload["messages"], [{"role": "assistant"}])
