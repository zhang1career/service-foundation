import logging

from common.consts.string_const import STRING_EMPTY
from common.utils.string_util import implode
from data_analyzer import settings


logger = logging.getLogger(__name__)


_SQL_FIND_SRC_LIST_BATCH = """
MATCH (s)-[:{r_type}]->(d:{d_label})
WHERE d.name IN [{d_names}]
RETURN DISTINCT s
"""


_SQL_FIND_DEST_LIST_BATCH = """
MATCH (s:{s_label})-[:{r_type}]->(d)
WHERE s.name IN [{s_names}]
RETURN DISTINCT d
"""


_SQL_CONTAIN_RELATION = """
MATCH (s:{s_label} {s_uniq_props}), (d:{d_label} {d_uniq_props})
RETURN EXISTS ((s)-[:{r_type}]->(d)) AS is_contain
"""


_SQL_DUPLICATE_NODE_WITH_RELATIONS = """
MATCH (n:{original_node_label} {original_node_uniq_props})
CALL apoc.refactor.cloneNodes([n], true)
YIELD output
SET output += {adding_props}
RETURN properties(output) AS new_node_props
"""


class KnowledgeGraphRepo:
    """
    KnowledgeGraph is a class that represents a knowledge graph.
    It provides methods to add nodes and edges, and to retrieve the graph data.

    NOTE:
      A node is identified by its label and unique priorities.
      An edge is identified by its type only.
    """

    def __init__(self, name: str = "neo4j"):
        # lazy load
        from common.drivers.neo4j_driver import Neo4jDriver
        # connect the text-filter-sensitive-dfa db
        self._driver = Neo4jDriver(settings.GRAPH_DB_HOST + ":" + settings.GRAPH_DB_PORT,
                                   "neo4j",
                                   settings.GRAPH_DB_PASSWORD,
                                   name)

    def find_node_list(self, node_label: str) -> list[dict]:
        """
        Find nodes in the knowledge graph.
        """
        node_list = self._driver.find_node_list(node_label)
        return node_list

    def add_or_update_path(self,
                           src_label: str,
                           src_uniq_props: dict,
                           rel_type: str,
                           rel_props: dict,
                           dest_label: str,
                           dest_uniq_props: dict) -> None:
        """
        Add a path to the knowledge graph.
        """
        # prepare data
        # todo: move checkage to service/controller level
        src = self._driver.find_node(src_label, src_uniq_props)
        if not src:
            src = self._driver.create_node(src_label, src_uniq_props)
        dest = self._driver.find_node(dest_label, dest_uniq_props)
        if not dest:
            dest = self._driver.create_node(dest_label, dest_uniq_props)
        rel = self._driver.find_an_edge(src, dest, rel_type)
        if rel:
            self._driver.update_edge(rel, rel_props)
            return
        # query
        self._driver.create_edge(src, dest, rel_type, rel_props)

    def find_src_list(self, dest_label: str, dest_uniq_props: dict, rel_type: str) -> list[dict]:
        """
        Find a node in the knowledge graph.
        """
        dest = self._driver.find_node(dest_label, dest_uniq_props)
        if not dest:
            return []
        src_list = self._driver.find_src_list_from_dest(dest, rel_type)
        if not src_list:
            return []
        # return
        return [{
            'label': list(src.labels)[0],
            'name': src['name'],
        } for src in src_list]

    def find_src_list_batch(self, dest_label: str, name_list: list[str], rel_type: str) -> list[dict]:
        # query
        query = _SQL_FIND_SRC_LIST_BATCH.format(
            d_label=dest_label,
            d_names=",".join("\'{name}\'".format(name=str(name)) for name in name_list),
            r_type=rel_type,
        )
        result_list = self._driver.run(query)
        if not result_list:
            return []
        # return, the property "s" is designated as returning value from SQL.
        return [result["s"] for result in result_list]

    def find_dest_list(self, src_label: str, src_uniq_props: dict, rel_type: str) -> list[dict]:
        """
        Find a node in the knowledge graph.
        """
        src = self._driver.find_node(src_label, src_uniq_props)
        if not src:
            return []
        dest_list = self._driver.find_dest_list_from_src(src, rel_type)
        if not dest_list:
            return []
        # return
        return [{
            'label': list(dest.labels)[0],
            'name': dest['name'],
        } for dest in dest_list]

    def find_dest_list_batch(self, src_label: str, name_list: list[str], rel_type: str) -> list[dict]:
        # query
        query = _SQL_FIND_DEST_LIST_BATCH.format(
            s_label=src_label,
            s_names=",".join("\'{name}\'".format(name=str(name)) for name in name_list),
            r_type=rel_type,
        )
        result_list = self._driver.run(query)
        if not result_list:
            return []
        # return, the property "d" is designated as returning value from SQL.
        return [result["d"] for result in result_list]

    def contain_relation(self,
                         src_label: str,
                         src_uniq_dict: dict,
                         dest_label: str,
                         dest_uniq_dict: dict,
                         rel_type: str) -> bool:
        # prepare data
        src_uniq_props = build_props_str(src_uniq_dict)
        dest_uniq_props = build_props_str(dest_uniq_dict)
        # query
        query = _SQL_CONTAIN_RELATION.format(
            s_label=src_label,
            s_uniq_props=src_uniq_props,
            d_label=dest_label,
            d_uniq_props=dest_uniq_props,
            r_type=rel_type,
        )
        result_list = self._driver.run(query)
        if not result_list:
            return False
        return [result["is_contain"] for result in result_list][0]

    def duplicate_node_with_relations(self,
                                      original_node_label: str,
                                      original_node_uniq_dict: dict,
                                      adding_dict: dict) -> dict[str, any]:
        # prepare data
        original_node_uniq_props = build_props_str(original_node_uniq_dict)
        adding_props = build_props_str(adding_dict)
        # query
        query = _SQL_DUPLICATE_NODE_WITH_RELATIONS.format(
            original_node_label=original_node_label,
            original_node_uniq_props=original_node_uniq_props,
            adding_props=adding_props
        )
        result_list = self._driver.run(query)
        if not result_list:
            return {}
        return [result["new_node_props"] for result in result_list][0]


def build_props_str(props: dict) -> str:
    """
    Build a string of properties for Cypher query.
    {"foo": "bar"} -> {foo: \'bar\'}
    """
    if not props:
        return STRING_EMPTY
    prop_list = []
    for key, value in props.items():
        if isinstance(value, int):
            prop_list.append(f"{key}: {value}")
            continue
        if isinstance(value, bool):
            value_bool = 'true' if value else 'false'
            prop_list.append(f"{key}: {value_bool}")
            continue
        prop_list.append(f"{key}: \'{value}\'")
    props_str = implode(prop_list)
    return f"{{{props_str}}}"


def build_props_cypher(owner: str, props: dict) -> str:
    """
    Build a cypher string of properties for Cypher query.
    {"foo": "bar"} -> owner.foo = \'bar\'
    """
    if not props:
        return STRING_EMPTY
    prop_list = []
    for key, value in props.items():
        if isinstance(value, int):
            prop_list.append(f"{owner}.{key}={value}")
            continue
        if isinstance(value, bool):
            value_bool = 'true' if value else 'false'
            prop_list.append(f"{owner}.{key}={value_bool}")
            continue
        prop_list.append(f"{owner}.{key}='{value}'")
    return implode(prop_list)
