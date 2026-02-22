"""
Unit tests for Neo4j connection module.
Neo4j and get_neo4j_client are mocked so no real Neo4j connection is used. Generated.
"""
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch, PropertyMock

from app_know.conn.neo4j import Neo4jClient, Neo4jConfig, get_neo4j_client


class TestNeo4jConfig(TestCase):
    """Tests for Neo4jConfig class."""

    def test_init_with_explicit_values(self):
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="test_user",
            password="test_pass",
            database="testdb",
        )
        self.assertEqual(config.uri, "bolt://localhost:7687")
        self.assertEqual(config.user, "test_user")
        self.assertEqual(config.password, "test_pass")
        self.assertEqual(config.database, "testdb")

    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://env.host:7687",
        "NEO4J_USER": "env_user",
        "NEO4J_PASS": "env_pass",
        "NEO4J_DATABASE": "envdb",
    })
    def test_init_from_environment(self):
        config = Neo4jConfig()
        self.assertEqual(config.uri, "bolt://env.host:7687")
        self.assertEqual(config.user, "env_user")
        self.assertEqual(config.password, "env_pass")
        self.assertEqual(config.database, "envdb")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_with_defaults(self):
        config = Neo4jConfig(user="u", password="p")
        self.assertEqual(config.uri, "bolt://localhost:7687")
        self.assertEqual(config.database, "neo4j")

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_uri(self):
        config = Neo4jConfig(user="user", password="pass")
        config.uri = None
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("NEO4J_URI", str(ctx.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_user(self):
        config = Neo4jConfig(uri="bolt://localhost:7687", user=None, password="pass")
        config.user = None  # ensure env cannot override for this test
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("NEO4J_USER", str(ctx.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_password(self):
        config = Neo4jConfig(uri="bolt://localhost:7687", user="user", password=None)
        config.password = None  # ensure env cannot override for this test
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("NEO4J_PASS", str(ctx.exception))

    def test_validate_success(self):
        config = Neo4jConfig(uri="bolt://localhost:7687", user="user", password="pass")
        self.assertTrue(config.validate())


class TestNeo4jClient(TestCase):
    """Tests for Neo4jClient class."""

    def setUp(self):
        self.config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="test_user",
            password="test_pass",
            database="testdb",
        )

    def test_init_with_config(self):
        client = Neo4jClient(self.config)
        self.assertEqual(client.config, self.config)

    @patch.dict(os.environ, {"NEO4J_USER": "u", "NEO4J_PASS": "p"})
    def test_init_without_config_uses_default(self):
        client = Neo4jClient()
        self.assertIsNotNone(client.config)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_connect_success(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = Neo4jClient(self.config)
        result = client.connect()

        self.assertEqual(result, client)
        mock_graph.assert_called_once()
        mock_graph_instance.run.assert_called_with("RETURN 1")

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    @patch.dict(os.environ, {}, clear=True)
    def test_connect_invalid_config_raises(
        self, mock_rel_matcher, mock_node_matcher, mock_graph
    ):
        """Invalid config raises ValueError; Graph/NodeMatcher/RelationshipMatcher mocked so no real Neo4j connection. Generated."""
        invalid_config = Neo4jConfig(uri="bolt://localhost:7687", user=None, password="p")
        invalid_config.user = None  # ensure env cannot override for this test
        client = Neo4jClient(invalid_config)

        with self.assertRaises(ValueError):
            client.connect()

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_disconnect(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = Neo4jClient(self.config)
        client.connect()
        client.disconnect()

        self.assertFalse(client.is_connected())

    def test_disconnect_when_not_connected(self):
        client = Neo4jClient(self.config)
        client.disconnect()

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_is_connected_true(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = Neo4jClient(self.config)
        client.connect()

        self.assertTrue(client.is_connected())

    def test_is_connected_false_when_not_connected(self):
        client = Neo4jClient(self.config)
        self.assertFalse(client.is_connected())

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_graph_property(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = Neo4jClient(self.config)
        client.connect()

        self.assertEqual(client.graph, mock_graph_instance)

    def test_graph_property_not_connected_raises(self):
        client = Neo4jClient(self.config)

        with self.assertRaises(ConnectionError):
            _ = client.graph

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    @patch("app_know.conn.neo4j.Node")
    def test_create_node(self, mock_node, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_node_instance = MagicMock()
        mock_node.return_value = mock_node_instance

        client = Neo4jClient(self.config)
        client.connect()
        result = client.create_node("Person", {"name": "Alice", "age": 30})

        mock_node.assert_called_once_with("Person", name="Alice", age=30)
        mock_graph_instance.create.assert_called_once_with(mock_node_instance)
        self.assertEqual(result, mock_node_instance)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    @patch("app_know.conn.neo4j.Relationship")
    def test_create_relationship(self, mock_rel, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_rel_instance = MagicMock()
        mock_rel.return_value = mock_rel_instance
        start_node = MagicMock()
        end_node = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        result = client.create_relationship(start_node, end_node, "KNOWS", {"since": 2020})

        mock_rel.assert_called_once_with(start_node, "KNOWS", end_node, since=2020)
        mock_graph_instance.create.assert_called_with(mock_rel_instance)
        self.assertEqual(result, mock_rel_instance)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_find_node(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_matcher_instance = MagicMock()
        mock_node_matcher.return_value = mock_matcher_instance
        mock_found_node = MagicMock()
        mock_matcher_instance.match.return_value.first.return_value = mock_found_node

        client = Neo4jClient(self.config)
        client.connect()
        result = client.find_node("Person", {"name": "Alice"})

        mock_matcher_instance.match.assert_called_once_with("Person", name="Alice")
        self.assertEqual(result, mock_found_node)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_find_nodes(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_matcher_instance = MagicMock()
        mock_node_matcher.return_value = mock_matcher_instance
        mock_nodes = [MagicMock(), MagicMock()]
        mock_matcher_instance.match.return_value.limit.return_value = mock_nodes

        client = Neo4jClient(self.config)
        client.connect()
        result = client.find_nodes("Person", {"city": "NYC"}, limit=50)

        mock_matcher_instance.match.assert_called_once_with("Person", city="NYC")
        mock_matcher_instance.match.return_value.limit.assert_called_once_with(50)
        self.assertEqual(len(result), 2)

    def test_find_node_not_connected_raises(self):
        client = Neo4jClient(self.config)

        with self.assertRaises(ConnectionError):
            client.find_node("Person", {"name": "Alice"})

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_find_relationship(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_matcher_instance = MagicMock()
        mock_rel_matcher.return_value = mock_matcher_instance
        mock_found_rel = MagicMock()
        mock_matcher_instance.match.return_value.first.return_value = mock_found_rel
        start_node = MagicMock()
        end_node = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        result = client.find_relationship(start_node, end_node, "KNOWS")

        mock_matcher_instance.match.assert_called_once_with(
            nodes=[start_node, end_node],
            r_type="KNOWS",
        )
        self.assertEqual(result, mock_found_rel)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_get_neighbors_outgoing(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_matcher_instance = MagicMock()
        mock_rel_matcher.return_value = mock_matcher_instance
        
        mock_rel1 = MagicMock()
        mock_rel1.end_node = MagicMock()
        mock_rel2 = MagicMock()
        mock_rel2.end_node = MagicMock()
        mock_matcher_instance.match.return_value.limit.return_value = [mock_rel1, mock_rel2]
        
        source_node = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        result = client.get_neighbors(source_node, "KNOWS", direction="outgoing")

        self.assertEqual(len(result), 2)
        self.assertIn(mock_rel1.end_node, result)
        self.assertIn(mock_rel2.end_node, result)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_update_node(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_node = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        result = client.update_node(mock_node, {"age": 35})

        mock_node.__setitem__.assert_called_once_with("age", 35)
        mock_graph_instance.push.assert_called_once_with(mock_node)
        self.assertEqual(result, mock_node)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_delete_node(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_node = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        client.delete_node(mock_node)

        mock_graph_instance.delete.assert_called_once_with(mock_node)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_delete_relationship(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_rel = MagicMock()

        client = Neo4jClient(self.config)
        client.connect()
        client.delete_relationship(mock_rel)

        mock_graph_instance.separate.assert_called_once_with(mock_rel)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_run_query(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_result = MagicMock()
        mock_graph_instance.run.return_value = mock_result

        client = Neo4jClient(self.config)
        client.connect()
        result = client.run("MATCH (n) RETURN n LIMIT $limit", {"limit": 10})

        mock_graph_instance.run.assert_called_with(
            "MATCH (n) RETURN n LIMIT $limit",
            {"limit": 10},
        )
        self.assertEqual(result, mock_result)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_count_nodes(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_result = MagicMock()
        mock_result.evaluate.return_value = 42
        mock_graph_instance.run.return_value = mock_result

        client = Neo4jClient(self.config)
        client.connect()
        count = client.count_nodes("Person")

        self.assertEqual(count, 42)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_count_relationships(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_result = MagicMock()
        mock_result.evaluate.return_value = 15
        mock_graph_instance.run.return_value = mock_result

        client = Neo4jClient(self.config)
        client.connect()
        count = client.count_relationships("KNOWS")

        self.assertEqual(count, 15)

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_context_manager(self, mock_rel_matcher, mock_node_matcher, mock_graph):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        with Neo4jClient(self.config) as client:
            self.assertIsNotNone(client)
            self.assertTrue(client.is_connected())

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    def test_context_manager_exception_still_disconnects(
        self, mock_rel_matcher, mock_node_matcher, mock_graph
    ):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        with self.assertRaises(RuntimeError):
            with Neo4jClient(self.config) as client:
                raise RuntimeError("Test error")


class TestGetNeo4jClient(TestCase):
    """Tests for get_neo4j_client factory function."""

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://factory.host:7687",
        "NEO4J_USER": "factory_user",
        "NEO4J_PASS": "factory_pass",
    })
    def test_get_neo4j_client_default(
        self, mock_rel_matcher, mock_node_matcher, mock_graph
    ):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = get_neo4j_client()

        self.assertIsNotNone(client)
        self.assertTrue(client.is_connected())

    @patch("app_know.conn.neo4j.Graph")
    @patch("app_know.conn.neo4j.NodeMatcher")
    @patch("app_know.conn.neo4j.RelationshipMatcher")
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://factory.host:7687",
        "NEO4J_USER": "factory_user",
        "NEO4J_PASS": "factory_pass",
    })
    def test_get_neo4j_client_with_database(
        self, mock_rel_matcher, mock_node_matcher, mock_graph
    ):
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance

        client = get_neo4j_client(database="custom_db")

        self.assertEqual(client.config.database, "custom_db")


def _make_mock_neo4j_client():
    """Build a mock Neo4jClient so tests never use real Neo4j connection. Generated."""
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.is_connected.return_value = True
    mock_client.disconnect.return_value = None
    mock_node = MagicMock()
    mock_node.__getitem__ = lambda self, k: getattr(self, "_props", {}).get(k)
    mock_node.__setitem__ = lambda self, k, v: setattr(self, "_props", getattr(self, "_props", {}) or {}) or (getattr(self, "_props", {}).__setitem__(k, v))
    mock_node._props = {}
    mock_client.create_node.return_value = mock_node
    mock_client.find_node.return_value = mock_node
    mock_client.find_node.side_effect = lambda *a, **kw: mock_node
    mock_client.create_relationship.return_value = MagicMock()
    mock_client.find_relationship.return_value = MagicMock()
    mock_client.get_neighbors.return_value = [MagicMock()]
    mock_client.update_node.return_value = mock_node
    return mock_client


class TestNeo4jClientIntegration(TestCase):
    """
    Integration-style tests for Neo4jClient using a mock client only.
    get_neo4j_client is patched so no real Neo4j connection is used. Generated.
    """

    @patch("app_know.tests.test_neo4j.get_neo4j_client")
    def test_real_connection(self, mock_get_neo4j):
        """Test connection behavior using mock (no real Neo4j)."""
        mock_client = _make_mock_neo4j_client()
        mock_get_neo4j.return_value = mock_client
        client = get_neo4j_client()
        self.assertTrue(client.is_connected())
        client.disconnect()
        mock_get_neo4j.assert_called_once()

    @patch("app_know.tests.test_neo4j.get_neo4j_client")
    def test_real_crud_operations(self, mock_get_neo4j):
        """Test CRUD operations using mock (no real Neo4j)."""
        mock_client = _make_mock_neo4j_client()
        mock_node = MagicMock()
        mock_node.__getitem__ = lambda s, k: {"name": "test_neo4j_crud", "value": 123}.get(k)
        mock_node.__setitem__ = MagicMock()
        mock_updated = MagicMock()
        mock_updated.__getitem__ = lambda s, k: {"name": "test_neo4j_crud", "value": 456}.get(k)
        mock_updated.__setitem__ = MagicMock()
        mock_client.create_node.return_value = mock_node
        mock_client.find_node.side_effect = [mock_node, mock_updated, None]
        mock_get_neo4j.return_value = mock_client
        client = get_neo4j_client()
        node = client.create_node("TestNode", {"name": "test_neo4j_crud", "value": 123})
        self.assertIsNotNone(node)
        found = client.find_node("TestNode", {"name": "test_neo4j_crud"})
        self.assertIsNotNone(found)
        self.assertEqual(found["value"], 123)
        client.update_node(found, {"value": 456})
        updated = client.find_node("TestNode", {"name": "test_neo4j_crud"})
        self.assertEqual(updated["value"], 456)
        client.delete_node(updated)
        deleted = client.find_node("TestNode", {"name": "test_neo4j_crud"})
        self.assertIsNone(deleted)
        client.disconnect()

    @patch("app_know.tests.test_neo4j.get_neo4j_client")
    def test_real_relationship_operations(self, mock_get_neo4j):
        """Test relationship operations using mock (no real Neo4j)."""
        mock_client = _make_mock_neo4j_client()
        mock_node1 = MagicMock()
        mock_node2 = MagicMock()
        mock_rel = MagicMock()
        mock_client.create_node.side_effect = [mock_node1, mock_node2]
        mock_client.create_relationship.return_value = mock_rel
        mock_client.find_relationship.return_value = mock_rel
        mock_client.get_neighbors.return_value = [mock_node2]
        mock_get_neo4j.return_value = mock_client
        client = get_neo4j_client()
        node1 = client.create_node("TestPerson", {"name": "Alice"})
        node2 = client.create_node("TestPerson", {"name": "Bob"})
        rel = client.create_relationship(node1, node2, "TEST_KNOWS", {"since": 2020})
        self.assertIsNotNone(rel)
        found_rel = client.find_relationship(node1, node2, "TEST_KNOWS")
        self.assertIsNotNone(found_rel)
        neighbors = client.get_neighbors(node1, "TEST_KNOWS", direction="outgoing")
        self.assertEqual(len(neighbors), 1)
        client.delete_relationship(rel)
        client.delete_node(node1)
        client.delete_node(node2)
        client.disconnect()
