"""
Graph Builder Agent: build Neo4j graph from sentence-level 主谓宾.
Creates (subject)-[predicate]->(object) edges per sentence, scoped by kid.
Nodes use sp_type=1 (名词/主语), edges use sp_type=2 (谓语) for candidate queries.
"""
import logging
import re
import time
import zlib
from typing import Any, Dict, List, Optional

from app_know.repos import knowledge_point_repo
from common.drivers.neo4j_driver import Neo4jDriver
from service_foundation import settings

logger = logging.getLogger(__name__)

# Neo4j 节点 label：成分分析 / 句子级主谓宾均使用此标签（在本文件此处定义）
LABEL_SVO_NODE = "svo_entity"
# 成分分析保存时按成分使用的节点 label（表达式与 Neo4j 统一：主/宾用 svo_core）
LABEL_SVO_CORE = "svo_core"  # 主语、宾语（核心节点）
LABEL_SVO_SUB = "svo_sub"  # 兼容旧数据
LABEL_SVO_OBJ = "svo_obj"  # 兼容旧数据
LABEL_SVO_ATTR = "svo_attr"  # 定语
LABEL_SVO_COMP = "svo_comp"  # 补语
# Default app_id for sentence graph (no multi-tenant)
APP_ID_SENTENCE = 0
# 成分分析保存到 Neo4j 时使用的 app_id
APP_ID_COMPONENTS = 1
# sp_type: 1=名词(主语/宾语), 2=谓语边, 3=定语节点, 10=补语节点/补语-宾语边, 11=定语-主语/定语-宾语边
SP_TYPE_NOUN = 1
SP_TYPE_PREDICATE = 2
SP_TYPE_ATTRIBUTIVE = 3
SP_TYPE_COMPLEMENT = 10
SP_TYPE_ATTRIB_TO_SUBJECT_OR_OBJECT = 11
# 定语->主语、定语->宾语 的边类型（本文件内定义，用于成分分析保存）
REL_TYPE_ATTRIBUTIVE_TO = "ATTR"
# 补语->宾语 的边类型
REL_TYPE_COMPLEMENTS = "COMP"


def _sanitize_rel_type(predicate: str) -> str:
    """Convert predicate to valid Neo4j relationship type."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", (predicate or "").strip())
    return s or "related_to"


_neo4j_driver: Optional[Neo4jDriver] = None


def _get_driver() -> Neo4jDriver:
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASS,
            name=settings.NEO4J_DATABASE,
        )
    return _neo4j_driver


def _node_key(name: str, kid: int) -> str:
    """Unique key for node lookup: (name, kid)."""
    n = (name or "").strip()
    return f"{kid}:{n}" if n else ""


def build_graph_for_knowledge(kid: int) -> Dict[str, Any]:
    """
    Build Neo4j graph from sentences with graph_subject, graph_object.
    Creates nodes for subject/object (per kid), edges for predicate.
    Returns {created_nodes, created_edges, skipped, errors}.
    """
    if kid is None or not isinstance(kid, int) or kid <= 0:
        raise ValueError("kid must be a positive integer")
    items, _ = knowledge_point_repo.list_by_batch(kid, limit=500)
    driver = _get_driver()
    nodes_cache: Dict[str, Any] = {}  # key -> Neo4j node
    created_nodes = 0
    created_edges = 0
    skipped = 0
    errors = []

    for s in items:
        subject = (s.graph_subject or "").strip()
        obj = (s.graph_object or "").strip()
        if not subject and not obj:
            skipped += 1
            continue
        # Infer predicate from graph_brief or use default
        pred = "related_to"
        if s.graph_brief:
            m = re.search(r"谓[：:]\s*(\S+)", s.graph_brief)
            if m:
                pred = m.group(1).strip() or pred
        pred_type = _sanitize_rel_type(pred)
        if not subject:
            subject = "_"
        if not obj:
            obj = "_"
        try:
            sub_key = _node_key(subject, kid)
            obj_key = _node_key(obj, kid)
            ut_ms = int(time.time() * 1000)
            if sub_key and sub_key not in nodes_cache:
                existing = driver.find_node(
                    LABEL_SVO_NODE,
                    {"name": subject, "kid": kid, "app_id": APP_ID_SENTENCE},
                )
                if existing:
                    driver.update_node(existing, {"sp_type": SP_TYPE_NOUN, "ut": ut_ms})
                    nodes_cache[sub_key] = existing
                else:
                    node = driver.create_node(
                        LABEL_SVO_NODE,
                        {
                            "name": subject,
                            "kid": kid,
                            "app_id": APP_ID_SENTENCE,
                            "sid": s.id,
                            "sp_type": SP_TYPE_NOUN,
                            "ut": ut_ms,
                        },
                    )
                    nodes_cache[sub_key] = node
                    created_nodes += 1
            if obj_key and obj_key not in nodes_cache:
                existing = driver.find_node(
                    LABEL_SVO_NODE,
                    {"name": obj, "kid": kid, "app_id": APP_ID_SENTENCE},
                )
                if existing:
                    driver.update_node(existing, {"sp_type": SP_TYPE_NOUN, "ut": ut_ms})
                    nodes_cache[obj_key] = existing
                else:
                    node = driver.create_node(
                        LABEL_SVO_NODE,
                        {
                            "name": obj,
                            "kid": kid,
                            "app_id": APP_ID_SENTENCE,
                            "sid": s.id,
                            "sp_type": SP_TYPE_NOUN,
                            "ut": ut_ms,
                        },
                    )
                    nodes_cache[obj_key] = node
                    created_nodes += 1
            sub_node = nodes_cache.get(sub_key)
            obj_node = nodes_cache.get(obj_key)
            if sub_node and obj_node:
                existing_edge = driver.find_an_edge(sub_node, obj_node, pred_type)
                if existing_edge is None:
                    driver.create_edge(
                        sub_node,
                        obj_node,
                        pred_type,
                        {
                            "kid": kid,
                            "sid": s.id,
                            "app_id": APP_ID_SENTENCE,
                            "sp_type": SP_TYPE_PREDICATE,
                            "ut": ut_ms,
                        },
                    )
                    created_edges += 1
                else:
                    driver.update_edge(existing_edge, {"sp_type": SP_TYPE_PREDICATE, "ut": ut_ms})
        except Exception as e:
            errors.append({"sentence_id": s.id, "error": str(e)})
            logger.warning("[graph_builder] Error for sentence %s: %s", s.id, e)

    return {
        "created_nodes": created_nodes,
        "created_edges": created_edges,
        "skipped": skipped,
        "errors": errors,
    }


def get_sentence_graph(kid: int) -> Dict[str, Any]:
    """
    Fetch Neo4j subgraph for knowledge (sentence-level svo_entity).
    Returns {nodes: [{id, label}], edges: [{from, to, label}]}.
    """
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return {"nodes": [], "edges": []}
    driver = _get_driver()
    query = """
        MATCH (n:""" + LABEL_SVO_NODE + """)-[r]-(m:""" + LABEL_SVO_NODE + """)
        WHERE n.kid = $kid AND m.kid = $kid AND n.app_id = $app_id AND m.app_id = $app_id
        RETURN startNode(r) AS startNode, endNode(r) AS endNode, type(r) AS rel_type
    """
    try:
        cursor = driver.run(query, {"kid": kid, "app_id": APP_ID_SENTENCE})
        nodes_map: Dict[str, Dict[str, Any]] = {}
        edges_list: List[Dict[str, Any]] = []
        seen_edges: set = set()
        for record in cursor:
            start_node = record["startNode"]
            end_node = record["endNode"]
            rel_type = record["rel_type"] or "related_to"
            start_name = (start_node.get("name", "?") or "?").strip()
            end_name = (end_node.get("name", "?") or "?").strip()
            start_id = str(start_node.identity) if hasattr(start_node, "identity") else str(id(start_node))
            end_id = str(end_node.identity) if hasattr(end_node, "identity") else str(id(end_node))
            if start_id not in nodes_map:
                nodes_map[start_id] = {"id": start_id, "label": start_name}
            if end_id not in nodes_map:
                nodes_map[end_id] = {"id": end_id, "label": end_name}
            key = (start_id, end_id, rel_type)
            if key not in seen_edges:
                seen_edges.add(key)
                edges_list.append({"from": start_id, "to": end_id, "label": rel_type})
        return {"nodes": list(nodes_map.values()), "edges": edges_list}
    except Exception as e:
        logger.exception("[graph_builder] get_sentence_graph error: %s", e)
        return {"nodes": [], "edges": []}


def get_top_noun_nodes(limit: int = 100) -> List[str]:
    """
    Query Neo4j for noun nodes (sp_type=1), ordered by recent update (ut desc), return distinct names.
    Used as candidate subject list for 摘要 single-choice extraction.
    """
    if limit <= 0 or limit > 500:
        limit = 100
    driver = _get_driver()
    query = """
        MATCH (n:""" + LABEL_SVO_NODE + """)
        WHERE n.sp_type = $sp_type AND n.name IS NOT NULL AND trim(n.name) <> ''
        WITH n.name AS name, max(COALESCE(n.ut, 0)) AS ut
        ORDER BY ut DESC
        LIMIT $limit
        RETURN name
    """
    try:
        cursor = driver.run(query, {"sp_type": SP_TYPE_NOUN, "limit": limit})
        return [str(r["name"]).strip() for r in cursor if r.get("name")]
    except Exception as e:
        logger.warning("[graph_builder] get_top_noun_nodes error: %s", e)
        return []


def get_top_predicate_edges(limit: int = 100) -> List[str]:
    """
    Query Neo4j for predicate edges (sp_type=2), ordered by recent update (ut desc), return distinct relationship types.
    Used as candidate predicate list for 摘要 single-choice extraction.
    """
    if limit <= 0 or limit > 500:
        limit = 100
    driver = _get_driver()
    # type(r) in py2neo returns the relationship type; we need to match any svo_entity-to-svo_entity edges with sp_type=2
    query = """
        MATCH (a:""" + LABEL_SVO_NODE + """)-[r]-(b:""" + LABEL_SVO_NODE + """)
        WHERE r.sp_type = $sp_type
        WITH type(r) AS pred, max(COALESCE(r.ut, 0)) AS ut
        ORDER BY ut DESC
        LIMIT $limit
        RETURN pred
    """
    try:
        cursor = driver.run(query, {"sp_type": SP_TYPE_PREDICATE, "limit": limit})
        return [str(r["pred"]).strip() for r in cursor if r.get("pred")]
    except Exception as e:
        logger.warning("[graph_builder] get_top_predicate_edges error: %s", e)
        return []


def graph_string_to_hash(s: str) -> int:
    """
    将 graph 表达式字符串转为 32 位有符号整数 hash，用于 knowledge 表 hash 字段。
    使用 CRC32，离散度好，且与 MySQL INT 兼容。
    """
    raw = (s or "").encode("utf-8")
    return zlib.crc32(raw)


def parse_g_brief_to_triple(g_brief: str) -> Optional[Dict[str, str]]:
    """
    从 g_brief 字符串解析出 (subject, predicate, object)。
    支持 (s:svo_core {name:'x'})-[r:`谓`]-(o:svo_core {name:'y'}) 或旧格式 svo_sub/svo_obj。
    返回 {"subject": str, "predicate": str, "object": str} 或 None。
    """
    if not g_brief or not isinstance(g_brief, str):
        return None
    s = g_brief.strip()
    # 主/宾：svo_core 或 svo_sub/svo_obj 的 name；第一个为主语，最后一个为宾语
    core_parts = list(re.finditer(r"(?:svo_core|svo_sub|svo_obj)\s*\{\s*name\s*:\s*['\"]([^'\"]*)['\"]", s))
    sub_m = core_parts[0] if len(core_parts) >= 1 else None
    obj_m = core_parts[-1] if len(core_parts) >= 2 else None
    pred_m = re.search(r"\[r\s*:\s*(?:`([^`]+)`|([a-zA-Z0-9_]+))\]", s)
    if not sub_m or not obj_m:
        return None
    subject = (sub_m.group(1) or "").strip()
    object_name = (obj_m.group(1) or "").strip()
    predicate = "related_to"
    if pred_m:
        quoted = pred_m.group(1)
        bare = pred_m.group(2)
        if quoted:
            raw = quoted.strip()
        elif bare:
            raw = bare.strip()
        else:
            raw = ""
        if raw:
            predicate = raw
    return {"subject": subject, "predicate": predicate, "object": object_name}


def build_cypher_union_from_g_brief_list(g_brief_list: List[str]) -> str:
    """
    从多条 g_brief 生成一条 Cypher：每条 MATCH (s:svo_core)-[r]-(o:svo_core) ... RETURN s, r, o，用 UNION 连接。
    用于观点页「关系查询」。表达式样式与 build_graph_expressions 一致。
    """
    triples = []
    for gb in (g_brief_list or []):
        if not (gb and str(gb).strip()):
            continue
        t = parse_g_brief_to_triple(str(gb).strip())
        if not t:
            continue
        sub_q = _cypher_escape_string(t["subject"] or "_")
        obj_q = _cypher_escape_string(t["object"] or "_")
        pred_cypher = _cypher_rel_type(t["predicate"] or "related_to")
        part = "MATCH (s:svo_core {name: '%s'})-[r:%s]-(o:svo_core {name: '%s'}) RETURN s, r, o" % (
            sub_q, pred_cypher, obj_q
        )
        triples.append(part)
    if not triples:
        return ""
    return " UNION ".join(triples)


def _cypher_escape_string(s: str) -> str:
    """Escape string for Cypher single-quoted literal."""
    if not s:
        return ""
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def _cypher_rel_type(rel_name: str) -> str:
    """Format relationship type for Cypher; use backticks if non-ASCII or special chars."""
    if not rel_name or not rel_name.strip():
        return "related_to"
    s = rel_name.strip()
    if re.match(r"^[a-zA-Z0-9_]+$", s):
        return s
    escaped = s.replace("\\", "\\\\").replace("`", "\\`")
    return "`" + escaped + "`"


def build_graph_expressions(
        attributive_subject: str = "",
        subject: str = "",
        adverbial: str = "",
        predicate: str = "",
        attributive_object: str = "",
        object_name: str = "",
        complement: str = "",
) -> Dict[str, str]:
    """
    Build 图表达式（固定样式）from 成分分析，存入 knowledge 表 g_brief / g_sub / g_obj.
    Returns { graph_brief, graph_subject, graph_object }.
    - graph_subject: (定语)-主语 → (attr:svo_attr {name:'a'})-[:ATTR]->(c:svo_core {name:'x'})
    - graph_object: (定语)-宾语-补语 → (attr:svo_attr {name:'b'})-[:ATTR]->(c:svo_core {name:'y'})<-[:COMP]-(comp:svo_comp {name:'c'})
    - graph_brief: 主语-谓语-宾语 → (s:svo_core {name:'x'})-[r:`谓`]-(o:svo_core {name:'y'})
    """
    sub = (subject or "").strip() or "_"
    obj = (object_name or "").strip() or "_"
    pred = (predicate or "").strip() or "related_to"
    attr_sub = (attributive_subject or "").strip()
    attr_obj = (attributive_object or "").strip()
    comp = (complement or "").strip()
    adv = (adverbial or "").strip()

    sub_q = _cypher_escape_string(sub)
    obj_q = _cypher_escape_string(obj)
    pred_cypher = _cypher_rel_type(pred)
    adv_q = _cypher_escape_string(adv)

    # graph_subject: (定语)-主语，固定 (attr:svo_attr)-[:ATTR]->(c:svo_core)
    if attr_sub:
        graph_subject = "(attr:svo_attr {name: '%s'})-[:ATTR]->(c:svo_core {name: '%s'})" % (
            _cypher_escape_string(attr_sub), sub_q
        )
    else:
        graph_subject = "(c:svo_core {name: '%s'})" % sub_q

    # graph_object: (定语)-宾语-补语，固定 (attr:svo_attr)-[:ATTR]->(c:svo_core)<-[:COMP]-(comp:svo_comp)
    if attr_obj and comp:
        graph_object = "(attr:svo_attr {name: '%s'})-[:ATTR]->(c:svo_core {name: '%s'})<-[:COMP]-(comp:svo_comp {name: '%s'})" % (
            _cypher_escape_string(attr_obj), obj_q, _cypher_escape_string(comp)
        )
    elif attr_obj:
        graph_object = "(attr:svo_attr {name: '%s'})-[:ATTR]->(c:svo_core {name: '%s'})" % (
            _cypher_escape_string(attr_obj), obj_q
        )
    elif comp:
        graph_object = "(c:svo_core {name: '%s'})<-[:COMP]-(comp:svo_comp {name: '%s'})" % (
            obj_q, _cypher_escape_string(comp)
        )
    else:
        graph_object = "(c:svo_core {name: '%s'})" % obj_q

    # graph_brief: 主语-谓语-宾语，固定 (s:svo_core)-[r:`谓`]-(o:svo_core)
    r_part = "r:%s" % pred_cypher
    if adv:
        r_part = "r:%s {deco: '%s'}" % (pred_cypher, adv_q)
    graph_brief = "(s:svo_core {name: '%s'})-[%s]-(o:svo_core {name: '%s'})" % (sub_q, r_part, obj_q)

    return {"graph_brief": graph_brief, "graph_subject": graph_subject, "graph_object": graph_object}


def build_components_query_cypher(
        attributive_subject: str = "",
        subject: str = "",
        adverbial: str = "",
        predicate: str = "",
        attributive_object: str = "",
        object_name: str = "",
        complement: str = "",
) -> str:
    """
    生成「成分关系」的完整查询 Cypher：定语(主)-主语-谓语{状语}-定语(宾)-宾语-补语。
    样式与 build_graph_expressions 一致：attr:svo_attr, s/o:svo_core, comp:svo_comp。
    """
    sub = (subject or "").strip() or "_"
    obj = (object_name or "").strip() or "_"
    pred = (predicate or "").strip() or "related_to"
    attr_sub = (attributive_subject or "").strip()
    attr_obj = (attributive_object or "").strip()
    comp = (complement or "").strip()
    adv = (adverbial or "").strip()

    sub_q = _cypher_escape_string(sub)
    obj_q = _cypher_escape_string(obj)
    pred_cypher = _cypher_rel_type(pred)
    adv_q = _cypher_escape_string(adv)

    match_parts = []
    if attr_sub:
        match_parts.append(
            "(attr_s:svo_attr {name: '%s'})-[r_attr_s:ATTR]->(s:svo_core {name: '%s'})"
            % (_cypher_escape_string(attr_sub), sub_q)
        )
    else:
        match_parts.append("(s:svo_core {name: '%s'})" % sub_q)

    r_part = "r:%s" % pred_cypher
    if adv:
        r_part = "r:%s {deco: '%s'}" % (pred_cypher, adv_q)
    match_parts.append("(s)-[%s]-(o:svo_core {name: '%s'})" % (r_part, obj_q))

    if attr_obj:
        match_parts.append(
            "(attr_o:svo_attr {name: '%s'})-[r_attr_o:ATTR]->(o)"
            % _cypher_escape_string(attr_obj)
        )
    if comp:
        match_parts.append(
            "(comp:svo_comp {name: '%s'})-[r_comp:COMP]->(o)"
            % _cypher_escape_string(comp)
        )

    return_parts = ["s", "r", "o"]
    if attr_sub:
        return_parts.extend(["attr_s", "r_attr_s"])
    if attr_obj:
        return_parts.extend(["attr_o", "r_attr_o"])
    if comp:
        return_parts.extend(["comp", "r_comp"])

    return "MATCH " + ", ".join(match_parts) + " RETURN " + ", ".join(return_parts)


def save_components(
        point_id: int,
        batch_id: int,
        attributive_subject: str = "",
        subject: str = "",
        adverbial: str = "",
        predicate: str = "",
        attributive_object: str = "",
        object_name: str = "",
        complement: str = "",
) -> Dict[str, Any]:
    """
    Save 成分分析 to Neo4j. 节点 label：主语 svo_sub、宾语 svo_obj、定语 svo_attr、补语 svo_comp。
    节点属性: name, kid, bid, app_id=1。谓语边的 type 为谓语的值（无 label 属性）；边上有 deco=状语。
    定语->主语/宾语 的 type 为 ATTR（本文件 REL_TYPE_ATTRIBUTIVE_TO）；补语->宾语 为 COMP。
    Returns { created_nodes, created_edges, errors }.
    """
    driver = _get_driver()
    ut_ms = int(time.time() * 1000)
    created_nodes = 0
    created_edges = 0
    errors = []
    kid = point_id  # 当前 knowledge 的 id
    bid = batch_id  # 当前 knowledge 的批次号
    subject = (subject or "").strip() or "_"
    object_name = (object_name or "").strip() or "_"
    predicate_raw = (predicate or "").strip() or "related_to"
    adverbial = (adverbial or "").strip()

    def ensure_node(name: str, node_label: str, sp_type: int):
        if not name or not name.strip():
            return None, False
        n = name.strip()
        existing = driver.find_node(
            node_label,
            {"name": n, "kid": kid, "app_id": APP_ID_COMPONENTS},
        )
        if existing:
            driver.update_node(existing, {"sp_type": sp_type, "bid": bid, "ut": ut_ms})
            return existing, False
        node = driver.create_node(
            node_label,
            {"name": n, "kid": kid, "bid": bid, "app_id": APP_ID_COMPONENTS, "sp_type": sp_type, "ut": ut_ms},
        )
        return node, True

    def ensure_edge(from_node, to_node, rel_type: str, sp_type: int):
        if not from_node or not to_node:
            return 0
        existing = driver.find_an_edge(from_node, to_node, rel_type)
        props = {"kid": kid, "bid": bid, "app_id": APP_ID_COMPONENTS, "sp_type": sp_type, "ut": ut_ms}
        if existing is None:
            driver.create_edge(from_node, to_node, rel_type, props)
            return 1
        driver.update_edge(existing, props)
        return 0

    try:
        sub_node, c1 = ensure_node(subject, LABEL_SVO_CORE, SP_TYPE_NOUN)
        obj_node, c2 = ensure_node(object_name, LABEL_SVO_CORE, SP_TYPE_NOUN)
        if c1:
            created_nodes += 1
        if c2:
            created_nodes += 1
        if sub_node and obj_node:
            existing_edge = driver.find_an_edge(sub_node, obj_node, predicate_raw)
            edge_props = {"kid": kid, "bid": bid, "app_id": APP_ID_COMPONENTS, "sp_type": SP_TYPE_PREDICATE,
                          "ut": ut_ms}
            if adverbial:
                edge_props["deco"] = adverbial
            if existing_edge is None:
                driver.create_edge(sub_node, obj_node, predicate_raw, edge_props)
                created_edges += 1
            else:
                driver.update_edge(existing_edge, edge_props)
        for name, label, sp in [
            ((attributive_subject or "").strip(), LABEL_SVO_ATTR, SP_TYPE_ATTRIBUTIVE),
            ((attributive_object or "").strip(), LABEL_SVO_ATTR, SP_TYPE_ATTRIBUTIVE),
            ((complement or "").strip(), LABEL_SVO_COMP, SP_TYPE_COMPLEMENT),
        ]:
            if name:
                _, created = ensure_node(name, label, sp)
                if created:
                    created_nodes += 1
        # 定语(主)->主语, 定语(宾)->宾语: sp_type=11；补语->宾语: sp_type=10
        attrib_sub_name = (attributive_subject or "").strip()
        if attrib_sub_name and sub_node:
            attr_sub_node, _ = ensure_node(attrib_sub_name, LABEL_SVO_ATTR, SP_TYPE_ATTRIBUTIVE)
            created_edges += ensure_edge(attr_sub_node, sub_node, REL_TYPE_ATTRIBUTIVE_TO,
                                         SP_TYPE_ATTRIB_TO_SUBJECT_OR_OBJECT)
        attrib_obj_name = (attributive_object or "").strip()
        if attrib_obj_name and obj_node:
            attr_obj_node, _ = ensure_node(attrib_obj_name, LABEL_SVO_ATTR, SP_TYPE_ATTRIBUTIVE)
            created_edges += ensure_edge(attr_obj_node, obj_node, REL_TYPE_ATTRIBUTIVE_TO,
                                         SP_TYPE_ATTRIB_TO_SUBJECT_OR_OBJECT)
        comp_name = (complement or "").strip()
        if comp_name and obj_node:
            comp_node, _ = ensure_node(comp_name, LABEL_SVO_COMP, SP_TYPE_COMPLEMENT)
            created_edges += ensure_edge(comp_node, obj_node, REL_TYPE_COMPLEMENTS, SP_TYPE_COMPLEMENT)
    except Exception as e:
        errors.append(str(e))
        logger.exception("[graph_builder] save_components error: %s", e)
    return {"created_nodes": created_nodes, "created_edges": created_edges, "errors": errors}


def _node_labels_to_type(node) -> Optional[str]:
    """从 py2neo Node 取第一个 label 作为 nodeType，供前端按类型着色。"""
    labels = getattr(node, "labels", None)
    if labels is not None:
        try:
            lst = list(labels)
            if lst:
                return str(lst[0])
        except Exception:
            pass
    return None


def _node_id(node) -> str:
    """统一从 Node 取 id：py2neo 用 identity，neo4j 官方驱动可能用 id 或 element_id。"""
    uid = getattr(node, "identity", None)
    if uid is not None:
        return str(uid)
    uid = getattr(node, "id", None)
    if uid is not None:
        return str(uid)
    uid = getattr(node, "element_id", None)
    if uid is not None:
        return str(uid)
    return str(id(node))


def _rel_type(rel) -> Optional[str]:
    """统一取关系类型：可能是属性或方法（如 py2neo 的 type）。"""
    t = getattr(rel, "type", None)
    if t is None:
        return None
    if callable(t):
        try:
            t = t()
        except Exception:
            return None
    return str(t) if t is not None else None


def _record_entries(record):
    """兼容不同 Record 实现：有的有 .items()，有的仅 .keys() + 下标。"""
    if hasattr(record, "items") and callable(getattr(record, "items")):
        try:
            return list(record.items())
        except Exception:
            pass
    if hasattr(record, "keys") and callable(getattr(record, "keys")):
        try:
            return [(k, record[k]) for k in record.keys()]
        except Exception:
            pass
    return []


def run_cypher_to_graph(cypher: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run Cypher and convert result to { nodes: [{id, label, nodeType?}], edges: [{from, to, label}] }
    for vis/nvl. nodeType 来自 Neo4j 节点首个 label，用于前端按类型着色（类 Neo4j Browser）。
    """
    if not cypher or not cypher.strip():
        return {"nodes": [], "edges": []}
    driver = _get_driver()
    params = params or {}
    try:
        cursor = driver.run(cypher.strip(), params)
        nodes_map: Dict[str, Dict[str, Any]] = {}
        edges_list: List[Dict[str, Any]] = []
        seen_edges: set = set()
        for record in cursor:
            for key, val in _record_entries(record):
                if val is None:
                    continue
                # 先识别边（py2neo 的 Relationship 也有 identity/get，若先判节点会被误当作节点，导致只出点不出边）
                if hasattr(val, "start_node") and hasattr(val, "end_node"):
                    try:
                        rel = val
                        st = rel.start_node
                        en = rel.end_node
                        sid = _node_id(st)
                        eid = _node_id(en)
                        rtype = _rel_type(rel)
                        if rtype is None:
                            rtype = getattr(rel, "__class__", type(rel)).__name__ or "REL"
                        # 排除自环（from == to）及误识别的 "Node" 类型边，但仍需把 start/end 加入 nodes_map（否则孤立节点会消失）
                        if sid != eid and rtype != "Node":
                            if (sid, eid, rtype) not in seen_edges:
                                seen_edges.add((sid, eid, rtype))
                                edges_list.append({"from": sid, "to": eid, "label": rtype})
                        for n in (st, en):
                            nid = _node_id(n)
                            if nid not in nodes_map:
                                name = nid
                                if hasattr(n, "get"):
                                    name = (n.get("name") or n.get("caption") or nid)
                                    if not isinstance(name, str):
                                        name = nid
                                node_type = _node_labels_to_type(n)
                                nodes_map[nid] = {"id": nid, "label": name}
                                if node_type:
                                    nodes_map[nid]["nodeType"] = node_type
                    except Exception as e:
                        logger.warning("[graph_builder] run_cypher_to_graph skip rel: %s", e)
                else:
                    # 再识别节点（有 identity/id/element_id 且可 .get 的视为节点）
                    uid = getattr(val, "identity", None) or getattr(val, "id", None) or getattr(val, "element_id", None)
                    if uid is not None and hasattr(val, "get"):
                        nid = str(uid)
                        if nid not in nodes_map:
                            name = (val.get("name") or val.get("caption") or nid)
                            node_type = _node_labels_to_type(val)
                            nodes_map[nid] = {"id": nid, "label": name if isinstance(name, str) else nid}
                            if node_type:
                                nodes_map[nid]["nodeType"] = node_type
        return {"nodes": list(nodes_map.values()), "edges": edges_list}
    except Exception as e:
        logger.exception("[graph_builder] run_cypher_to_graph error: %s", e)
        return {"nodes": [], "edges": [], "error": str(e)}
