"""
Graph Builder Agent: build Neo4j graph from sentence-level 主谓宾.
Creates (subject)-[predicate]->(object) edges per sentence, scoped by kid.
Nodes use sp_type=1 (名词/主语), edges use sp_type=2 (谓语) for candidate queries.
"""
import logging
import re
import time
from typing import Any, Dict, List, Optional

from common.drivers.neo4j_driver import Neo4jDriver
from service_foundation import settings

from app_know.repos import knowledge_point_repo

logger = logging.getLogger(__name__)

# Neo4j 节点 label：成分分析 / 句子级主谓宾均使用此标签（在本文件此处定义）
LABEL_SVO_NODE = "svo_entity"
# 成分分析保存时按成分使用的节点 label
LABEL_SVO_SUB = "svo_sub"   # 主语
LABEL_SVO_OBJ = "svo_obj"   # 宾语
LABEL_SVO_ATTR = "svo_attr" # 定语
LABEL_SVO_COMP = "svo_comp" # 补语
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
    Build Neo4j 内连表达式（仅条件部分）from 成分分析，存入 knowledge 表.
    Returns { graph_brief, graph_subject, graph_object }.
    - graph_brief: (定语)-主语-谓语-(定语)-宾语-(补语)，如 (s:svo_sub {name:'x'})-[r:`谓`]-(o:svo_obj {name:'y'})
    - graph_subject: (定语)-主语，如 (attr:svo_attr {name:'a'})-[:ATTR]->(s:svo_sub {name:'x'})
    - graph_object: (定语)-宾语-(补语)，如 (attr_o:svo_attr {name:'b'})-[:ATTR]->(o:svo_obj {name:'y'}), (comp:svo_comp {name:'c'})-[:COMP]->(o)
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

    # graph_subject: 仅内连表达式 (定语)-主语
    if attr_sub:
        graph_subject = "(attr:svo_attr {name: '%s'})-[:%s]->(s:svo_sub {name: '%s'})" % (
            _cypher_escape_string(attr_sub), REL_TYPE_ATTRIBUTIVE_TO, sub_q
        )
    else:
        graph_subject = "(s:svo_sub {name: '%s'})" % sub_q

    # graph_object: 仅内连表达式 (定语)-宾语-(补语)
    parts_obj = []
    if attr_obj:
        parts_obj.append("(attr_o:svo_attr {name: '%s'})-[:%s]->(o:svo_obj {name: '%s'})" % (
            _cypher_escape_string(attr_obj), REL_TYPE_ATTRIBUTIVE_TO, obj_q
        ))
    else:
        parts_obj.append("(o:svo_obj {name: '%s'})" % obj_q)
    if comp:
        parts_obj.append("(comp:svo_comp {name: '%s'})-[:%s]->(o)" % (_cypher_escape_string(comp), REL_TYPE_COMPLEMENTS))
    graph_object = ", ".join(parts_obj)

    # graph_brief: 仅内连表达式 (定语)-主语-谓语-(定语)-宾语-(补语)，谓语边可带 decr=状语
    r_part = "r:%s" % pred_cypher
    if adv:
        r_part = "r:%s {decr: '%s'}" % (pred_cypher, adv_q)
    main = "(s:svo_sub {name: '%s'})-[%s]-(o:svo_obj {name: '%s'})" % (sub_q, r_part, obj_q)
    parts_brief = [main]
    if attr_sub:
        parts_brief.insert(0, "(attr_s:svo_attr {name: '%s'})-[:%s]->(s)" % (_cypher_escape_string(attr_sub), REL_TYPE_ATTRIBUTIVE_TO))
    if attr_obj:
        parts_brief.append("(attr_o:svo_attr {name: '%s'})-[:%s]->(o)" % (_cypher_escape_string(attr_obj), REL_TYPE_ATTRIBUTIVE_TO))
    if comp:
        parts_brief.append("(comp:svo_comp {name: '%s'})-[:%s]->(o)" % (_cypher_escape_string(comp), REL_TYPE_COMPLEMENTS))
    graph_brief = ", ".join(parts_brief)

    return {"graph_brief": graph_brief, "graph_subject": graph_subject, "graph_object": graph_object}


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
    节点属性: name, kid, bid, app_id=1。谓语边的 type 为谓语的值（无 label 属性）；边上有 decr=状语。
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
        sub_node, c1 = ensure_node(subject, LABEL_SVO_SUB, SP_TYPE_NOUN)
        obj_node, c2 = ensure_node(object_name, LABEL_SVO_OBJ, SP_TYPE_NOUN)
        if c1:
            created_nodes += 1
        if c2:
            created_nodes += 1
        if sub_node and obj_node:
            existing_edge = driver.find_an_edge(sub_node, obj_node, predicate_raw)
            edge_props = {"kid": kid, "bid": bid, "app_id": APP_ID_COMPONENTS, "sp_type": SP_TYPE_PREDICATE, "ut": ut_ms}
            if adverbial:
                edge_props["decr"] = adverbial
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
            created_edges += ensure_edge(attr_sub_node, sub_node, REL_TYPE_ATTRIBUTIVE_TO, SP_TYPE_ATTRIB_TO_SUBJECT_OR_OBJECT)
        attrib_obj_name = (attributive_object or "").strip()
        if attrib_obj_name and obj_node:
            attr_obj_node, _ = ensure_node(attrib_obj_name, LABEL_SVO_ATTR, SP_TYPE_ATTRIBUTIVE)
            created_edges += ensure_edge(attr_obj_node, obj_node, REL_TYPE_ATTRIBUTIVE_TO, SP_TYPE_ATTRIB_TO_SUBJECT_OR_OBJECT)
        comp_name = (complement or "").strip()
        if comp_name and obj_node:
            comp_node, _ = ensure_node(comp_name, LABEL_SVO_COMP, SP_TYPE_COMPLEMENT)
            created_edges += ensure_edge(comp_node, obj_node, REL_TYPE_COMPLEMENTS, SP_TYPE_COMPLEMENT)
    except Exception as e:
        errors.append(str(e))
        logger.exception("[graph_builder] save_components error: %s", e)
    return {"created_nodes": created_nodes, "created_edges": created_edges, "errors": errors}


def run_cypher_to_graph(cypher: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run Cypher and convert result to { nodes: [{id, label}], edges: [{from, to, label}] }
    for vis/nvl. Expects query to return records with node/rel/node or similar; extracts nodes and edges.
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
            for key, val in record.items():
                if val is None:
                    continue
                node_id = getattr(val, "identity", None)
                if node_id is not None and hasattr(val, "get"):
                    nid = str(node_id)
                    if nid not in nodes_map:
                        name = (val.get("name") or val.get("caption") or nid)
                        if isinstance(name, str):
                            nodes_map[nid] = {"id": nid, "label": name}
                        else:
                            nodes_map[nid] = {"id": nid, "label": nid}
                elif hasattr(val, "start_node") and hasattr(val, "end_node") and hasattr(val, "type"):
                    try:
                        rel = val
                        st = rel.start_node
                        en = rel.end_node
                        sid = str(getattr(st, "identity", id(st)))
                        eid = str(getattr(en, "identity", id(en)))
                        rtype = getattr(rel, "type", None) or getattr(rel, "__class__", {}).__name__ or "REL"
                        if isinstance(rtype, str) and (sid, eid, rtype) not in seen_edges:
                            seen_edges.add((sid, eid, rtype))
                            edges_list.append({"from": sid, "to": eid, "label": rtype})
                        for n in (st, en):
                            nid = str(getattr(n, "identity", id(n)))
                            if nid not in nodes_map and hasattr(n, "get"):
                                name = (n.get("name") or n.get("caption") or nid)
                                nodes_map[nid] = {"id": nid, "label": name if isinstance(name, str) else nid}
                    except Exception:
                        pass
        return {"nodes": list(nodes_map.values()), "edges": edges_list}
    except Exception as e:
        logger.exception("[graph_builder] run_cypher_to_graph error: %s", e)
        return {"nodes": [], "edges": [], "error": str(e)}
