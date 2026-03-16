"""
Parse Neo4j-style graph expressions (graph_subject, graph_object) into short sentences.
Rule: 定语-主语 / 定语-宾语 use "的" between; 宾语-补语 connect directly.
Example: (attr_o:svo_attr {name: '美国'})-[:ATTR]->(o:svo_obj {name: '产业革命'}) -> "美国的产业革命"
"""
import re
from typing import List


def _extract_names(expr: str) -> List[str]:
    """Extract node name values from expression in left-to-right order.
    Supports {name: 'x'}, {name: \"x\"}, and { name: 'x' }.
    """
    if not expr or not isinstance(expr, str):
        return []
    text = expr.strip()
    if not text:
        return []
    # Match { name: '...' } or { name: "..." } (single or double quote)
    pattern = r"\{\s*name\s*:\s*(?:'([^']*)'|\"([^\"]*)\")\s*\}"
    names = []
    for m in re.finditer(pattern, text):
        names.append((m.group(1) or m.group(2) or "").strip())
    return names


def graph_expr_to_sentence(expr: str) -> str:
    """
    Build short sentence from graph expression (定语-主语 or 定语-宾语-补语).
    - Between 定语 and 主语/宾语: add "的".
    - Between 宾语 and 补语: no separator (direct).
    So: names [a, b] -> "a的b"; names [a, b, c] -> "a的b" + "c" -> "a的bc".
    """
    names = _extract_names(expr)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    # first "的" second, then rest concatenated
    return names[0] + "的" + names[1] + "".join(names[2:])
