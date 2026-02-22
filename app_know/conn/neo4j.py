"""
Neo4j connection module for app_know.
Provides a configured Neo4j client for knowledge graph operations.
"""
import logging
import os
from typing import Optional, Any

from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher

logger = logging.getLogger(__name__)


class Neo4jConfig:
    """Configuration for Neo4j connection."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER")
        self.password = password or os.environ.get("NEO4J_PASS")
        self.database = database or os.environ.get("NEO4J_DATABASE", "neo4j")

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.uri:
            raise ValueError("NEO4J_URI is required")
        if not self.user:
            raise ValueError("NEO4J_USER is required")
        if not self.password:
            raise ValueError("NEO4J_PASS is required")
        return True


class Neo4jClient:
    """Neo4j client with connection management for knowledge graph operations."""

    def __init__(self, config: Optional[Neo4jConfig] = None):
        self._config = config or Neo4jConfig()
        self._graph: Optional[Graph] = None
        self._node_matcher: Optional[NodeMatcher] = None
        self._rel_matcher: Optional[RelationshipMatcher] = None

    @property
    def config(self) -> Neo4jConfig:
        return self._config

    def connect(self) -> "Neo4jClient":
        """
        Establish connection to Neo4j database.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If configuration is invalid.
            Exception: If connection fails.
        """
        self._config.validate()

        try:
            self._graph = Graph(
                self._config.uri,
                auth=(self._config.user, self._config.password),
                name=self._config.database,
            )
            self._graph.run("RETURN 1")
            self._node_matcher = NodeMatcher(self._graph)
            self._rel_matcher = RelationshipMatcher(self._graph)
            logger.info(f"Connected to Neo4j: {self._config.uri}/{self._config.database}")
            return self
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def disconnect(self) -> None:
        """Close the Neo4j connection."""
        self._graph = None
        self._node_matcher = None
        self._rel_matcher = None
        logger.info("Disconnected from Neo4j")

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if not self._graph:
            return False
        try:
            self._graph.run("RETURN 1")
            return True
        except Exception:
            return False

    @property
    def graph(self) -> Graph:
        """Get the underlying Graph instance."""
        if not self._graph:
            raise ConnectionError("Not connected to Neo4j")
        return self._graph

    def run(self, query: str, parameters: Optional[dict] = None) -> Any:
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            Query result.
        """
        if parameters is None:
            parameters = {}
        return self.graph.run(query, parameters)

    def create_node(self, label: str, properties: dict) -> Node:
        """
        Create a new node with the given label and properties.

        Args:
            label: Node label.
            properties: Node properties.

        Returns:
            Created Node instance.
        """
        node = Node(label, **properties)
        self.graph.create(node)
        logger.debug(f"Created node: {label} with properties {properties}")
        return node

    def create_relationship(
        self,
        start_node: Node,
        end_node: Node,
        rel_type: str,
        properties: Optional[dict] = None,
    ) -> Relationship:
        """
        Create a relationship between two nodes.

        Args:
            start_node: Source node.
            end_node: Target node.
            rel_type: Relationship type.
            properties: Optional relationship properties.

        Returns:
            Created Relationship instance.
        """
        if properties is None:
            properties = {}
        relationship = Relationship(start_node, rel_type, end_node, **properties)
        self.graph.create(relationship)
        logger.debug(f"Created relationship: {rel_type}")
        return relationship

    def find_node(self, label: str, properties: Optional[dict] = None) -> Optional[Node]:
        """
        Find a single node matching the label and properties.

        Args:
            label: Node label.
            properties: Properties to match.

        Returns:
            Node if found, None otherwise.
        """
        if not self._node_matcher:
            raise ConnectionError("Not connected to Neo4j")
        if properties is None:
            properties = {}
        return self._node_matcher.match(label, **properties).first()

    def find_nodes(
        self,
        label: str,
        properties: Optional[dict] = None,
        limit: int = 100,
    ) -> list[Node]:
        """
        Find multiple nodes matching the label and properties.

        Args:
            label: Node label.
            properties: Properties to match.
            limit: Maximum number of results.

        Returns:
            List of matching nodes.
        """
        if not self._node_matcher:
            raise ConnectionError("Not connected to Neo4j")
        if properties is None:
            properties = {}
        return list(self._node_matcher.match(label, **properties).limit(limit))

    def find_relationship(
        self,
        start_node: Optional[Node],
        end_node: Optional[Node],
        rel_type: str,
    ) -> Optional[Relationship]:
        """
        Find a single relationship between nodes.

        Args:
            start_node: Source node (None for any).
            end_node: Target node (None for any).
            rel_type: Relationship type.

        Returns:
            Relationship if found, None otherwise.
        """
        if not self._rel_matcher:
            raise ConnectionError("Not connected to Neo4j")
        return self._rel_matcher.match(
            nodes=[start_node, end_node],
            r_type=rel_type,
        ).first()

    def find_relationships(
        self,
        start_node: Optional[Node],
        end_node: Optional[Node],
        rel_type: str,
        limit: int = 100,
    ) -> list[Relationship]:
        """
        Find multiple relationships between nodes.

        Args:
            start_node: Source node (None for any).
            end_node: Target node (None for any).
            rel_type: Relationship type.
            limit: Maximum number of results.

        Returns:
            List of matching relationships.
        """
        if not self._rel_matcher:
            raise ConnectionError("Not connected to Neo4j")
        return list(
            self._rel_matcher.match(
                nodes=[start_node, end_node],
                r_type=rel_type,
            ).limit(limit)
        )

    def get_neighbors(
        self,
        node: Node,
        rel_type: str,
        direction: str = "outgoing",
        limit: int = 100,
    ) -> list[Node]:
        """
        Get neighboring nodes connected by a relationship.

        Args:
            node: Source node.
            rel_type: Relationship type.
            direction: 'outgoing', 'incoming', or 'both'.
            limit: Maximum number of results.

        Returns:
            List of neighboring nodes.
        """
        if not self._rel_matcher:
            raise ConnectionError("Not connected to Neo4j")

        results = []
        if direction in ("outgoing", "both"):
            rels = self._rel_matcher.match(nodes=[node, None], r_type=rel_type).limit(limit)
            results.extend([rel.end_node for rel in rels])
        if direction in ("incoming", "both"):
            rels = self._rel_matcher.match(nodes=[None, node], r_type=rel_type).limit(limit)
            results.extend([rel.start_node for rel in rels])
        return results

    def update_node(self, node: Node, properties: dict) -> Node:
        """
        Update node properties.

        Args:
            node: Node to update.
            properties: New properties.

        Returns:
            Updated node.
        """
        for key, value in properties.items():
            node[key] = value
        self.graph.push(node)
        return node

    def update_relationship(self, relationship: Relationship, properties: dict) -> Relationship:
        """
        Update relationship properties.

        Args:
            relationship: Relationship to update.
            properties: New properties.

        Returns:
            Updated relationship.
        """
        for key, value in properties.items():
            relationship[key] = value
        self.graph.push(relationship)
        return relationship

    def delete_node(self, node: Node) -> None:
        """Delete a node (must have no relationships)."""
        self.graph.delete(node)
        logger.debug(f"Deleted node: {node}")

    def delete_relationship(self, relationship: Relationship) -> None:
        """Delete a relationship."""
        self.graph.separate(relationship)
        logger.debug(f"Deleted relationship: {relationship}")

    def delete_all(self) -> None:
        """Delete all nodes and relationships (use with caution)."""
        self.graph.delete_all()
        logger.warning("Deleted all nodes and relationships")

    def count_nodes(self, label: Optional[str] = None) -> int:
        """
        Count nodes, optionally filtered by label.

        Args:
            label: Optional label to filter by.

        Returns:
            Number of nodes.
        """
        if label:
            result = self.run(f"MATCH (n:{label}) RETURN count(n) as count")
        else:
            result = self.run("MATCH (n) RETURN count(n) as count")
        return result.evaluate()

    def count_relationships(self, rel_type: Optional[str] = None) -> int:
        """
        Count relationships, optionally filtered by type.

        Args:
            rel_type: Optional relationship type to filter by.

        Returns:
            Number of relationships.
        """
        if rel_type:
            result = self.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
        else:
            result = self.run("MATCH ()-[r]->() RETURN count(r) as count")
        return result.evaluate()

    def __enter__(self) -> "Neo4jClient":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()


def get_neo4j_client(database: Optional[str] = None) -> Neo4jClient:
    """
    Factory function to create and connect a Neo4jClient.

    Args:
        database: Optional database name (defaults to NEO4J_DATABASE env var).

    Returns:
        Connected Neo4jClient instance.
    """
    config = Neo4jConfig(database=database)
    client = Neo4jClient(config)
    return client.connect()
