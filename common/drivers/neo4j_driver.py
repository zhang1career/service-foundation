from py2neo import Node, Relationship, Graph, NodeMatcher, RelationshipMatcher

from common.components.singleton import Singleton


class Neo4jDriver(Singleton):
    def __init__(self, uri, user, password, name="neo4j"):
        self._client = Graph(uri, auth=(user, password), name=name)
        self._rel_matcher = RelationshipMatcher(self._client)

    def create_node(self, label, properties):
        node = Node(label, **properties)
        self._client.create(node)
        return node

    def create_edge(self, start_node, end_node, rel_type, properties=None):
        if properties is None:
            properties = {}
        relationship = Relationship(start_node, rel_type, end_node, **properties)
        self._client.create(relationship)
        return relationship

    def update_node(self, node, properties):
        for key, value in properties.items():
            node[key] = value
        self._client.push(node)
        return node

    def update_edge(self, edge, properties):
        for key, value in properties.items():
            edge[key] = value
        self._client.push(edge)
        return edge

    def delete_node(self, node):
        self._client.delete(node)

    def delete_edge(self, edge):
        self._client.separate(edge)

    def delete_all(self):
        self._client.delete_all()

    def find_node(self, label, properties):
        matcher = NodeMatcher(self._client)
        return matcher.match(label, **properties).first()

    def find_node_list(self, label, properties={}, limit=1000):
        matcher = NodeMatcher(self._client)
        return matcher.match(label, **properties).limit(limit)

    def find_an_edge(self, start_node, end_node, rel_type):
        return self._rel_matcher.match(nodes=[start_node, end_node], r_type=rel_type).first()

    def find_src_list_from_dest(self, dest_node, rel_type, limit=1000) -> list[Node]:
        result = self._rel_matcher.match(nodes=[None, dest_node], r_type=rel_type).limit(limit)
        return [edge.start_node for edge in result]

    def find_dest_list_from_src(self, start_node, rel_type, limit=1000) -> list[Node]:
        result = self._rel_matcher.match(nodes=[start_node, None], r_type=rel_type).limit(limit)
        return [edge.end_node for edge in result]

    def run(self, query, parameters=None):
        if parameters is None:
            parameters = {}
        return self._client.run(query, parameters)
