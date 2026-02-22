"""
Unit tests for MongoDB Atlas connection module.
Atlas and get_atlas_client are mocked so no real DNS or MongoDB Atlas connection is used. Generated.
"""
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pymongo.errors import ConnectionFailure

from app_know.conn.atlas import AtlasClient, AtlasConfig, get_atlas_client


class TestAtlasConfig(TestCase):
    """Tests for AtlasConfig class."""

    def test_init_with_explicit_values(self):
        config = AtlasConfig(
            user="test_user",
            password="test_pass",
            host="test.mongodb.net",
            cluster="testcluster",
            db_name="testdb",
        )
        self.assertEqual(config.user, "test_user")
        self.assertEqual(config.password, "test_pass")
        self.assertEqual(config.host, "test.mongodb.net")
        self.assertEqual(config.cluster, "testcluster")
        self.assertEqual(config.db_name, "testdb")

    @patch.dict(os.environ, {
        "MONGO_ATLAS_USER": "env_user",
        "MONGO_ATLAS_PASS": "env_pass",
        "MONGO_ATLAS_HOST": "env.mongodb.net",
        "MONGO_ATLAS_CLUSTER": "envcluster",
        "MONGO_ATLAS_DB": "envdb",
    })
    def test_init_from_environment(self):
        config = AtlasConfig()
        self.assertEqual(config.user, "env_user")
        self.assertEqual(config.password, "env_pass")
        self.assertEqual(config.host, "env.mongodb.net")
        self.assertEqual(config.cluster, "envcluster")
        self.assertEqual(config.db_name, "envdb")

    def test_init_with_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AtlasConfig(user="u", password="p")
            self.assertEqual(config.host, "cluster.mongodb.net")
            self.assertEqual(config.cluster, "cluster0")
            self.assertEqual(config.db_name, "know")

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_user(self):
        config = AtlasConfig(user=None, password="pass", host="host")
        config.user = None  # ensure env cannot override for this test
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("MONGO_ATLAS_USER", str(ctx.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_password(self):
        config = AtlasConfig(user="user", password=None, host="host")
        config.password = None  # ensure env cannot override for this test
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("MONGO_ATLAS_PASS", str(ctx.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_host(self):
        config = AtlasConfig(user="user", password="pass")
        config.host = None
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("MONGO_ATLAS_HOST", str(ctx.exception))

    def test_validate_success(self):
        config = AtlasConfig(user="user", password="pass", host="host")
        self.assertTrue(config.validate())

    def test_uri_property(self):
        config = AtlasConfig(
            user="myuser",
            password="mypass",
            host="example.mongodb.net",
            cluster="mycluster",
        )
        expected = (
            "mongodb+srv://myuser:mypass@mycluster.example.mongodb.net/"
            "?retryWrites=true&w=majority&appName=Cluster0"
        )
        self.assertEqual(config.uri, expected)


class TestAtlasClient(TestCase):
    """Tests for AtlasClient class."""

    def setUp(self):
        self.config = AtlasConfig(
            user="test_user",
            password="test_pass",
            host="test.mongodb.net",
            cluster="testcluster",
            db_name="testdb",
        )

    def test_init_with_config(self):
        client = AtlasClient(self.config)
        self.assertEqual(client.config, self.config)

    def test_init_without_config_uses_default(self):
        with patch.dict(os.environ, {"MONGO_ATLAS_USER": "u", "MONGO_ATLAS_PASS": "p"}):
            client = AtlasClient()
            self.assertIsNotNone(client.config)

    @patch("app_know.conn.atlas.MongoClient")
    def test_connect_success(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        result = client.connect()

        self.assertEqual(result, client)
        mock_mongo_client.assert_called_once()
        mock_client.admin.command.assert_called_with("ping")

    @patch("app_know.conn.atlas.MongoClient")
    def test_connect_with_custom_timeout(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect(timeout_ms=10000)

        call_kwargs = mock_mongo_client.call_args[1]
        self.assertEqual(call_kwargs["serverSelectionTimeoutMS"], 10000)

    @patch.dict(os.environ, {}, clear=True)
    @patch("app_know.conn.atlas.MongoClient")
    def test_connect_invalid_config_raises(self, mock_mongo_client):
        """Invalid config raises ValueError; MongoClient is mocked so no real DNS/connection."""
        invalid_config = AtlasConfig(user=None, password="p", host="h")
        invalid_config.user = None  # ensure env cannot override
        client = AtlasClient(invalid_config)

        with self.assertRaises(ValueError):
            client.connect()
        mock_mongo_client.assert_not_called()

    @patch("app_know.conn.atlas.MongoClient")
    def test_disconnect(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()
        client.disconnect()

        mock_client.close.assert_called_once()

    def test_disconnect_when_not_connected(self):
        client = AtlasClient(self.config)
        client.disconnect()

    @patch("app_know.conn.atlas.MongoClient")
    def test_is_connected_true(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()

        self.assertTrue(client.is_connected())

    def test_is_connected_false_when_not_connected(self):
        client = AtlasClient(self.config)
        self.assertFalse(client.is_connected())

    @patch("app_know.conn.atlas.MongoClient")
    def test_is_connected_false_when_ping_fails(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = [{"ok": 1}, Exception("ping failed")]
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()

        self.assertFalse(client.is_connected())

    @patch("app_know.conn.atlas.MongoClient")
    def test_ping_success(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()

        self.assertTrue(client.ping())

    def test_ping_not_connected_raises(self):
        client = AtlasClient(self.config)

        with self.assertRaises(ConnectionFailure):
            client.ping()

    @patch("app_know.conn.atlas.MongoClient")
    def test_client_property(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()

        self.assertEqual(client.client, mock_client)

    def test_client_property_not_connected_raises(self):
        client = AtlasClient(self.config)

        with self.assertRaises(ConnectionFailure):
            _ = client.client

    @patch("app_know.conn.atlas.MongoClient")
    def test_db_property(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()

        self.assertEqual(client.db, mock_db)

    def test_db_property_not_connected_raises(self):
        client = AtlasClient(self.config)

        with self.assertRaises(ConnectionFailure):
            _ = client.db

    @patch("app_know.conn.atlas.MongoClient")
    def test_get_collection(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()
        result = client.get_collection("test_coll")

        self.assertEqual(result, mock_collection)
        mock_db.__getitem__.assert_called_with("test_coll")

    @patch("app_know.conn.atlas.MongoClient")
    def test_list_databases(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client.list_database_names.return_value = ["admin", "local", "testdb"]
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()
        result = client.list_databases()

        self.assertEqual(result, ["admin", "local", "testdb"])

    @patch("app_know.conn.atlas.MongoClient")
    def test_list_collections(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = ["coll1", "coll2"]
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client

        client = AtlasClient(self.config)
        client.connect()
        result = client.list_collections()

        self.assertEqual(result, ["coll1", "coll2"])

    @patch("app_know.conn.atlas.MongoClient")
    def test_context_manager(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        with AtlasClient(self.config) as client:
            self.assertIsNotNone(client)
            mock_client.admin.command.assert_called()

        mock_client.close.assert_called_once()

    @patch("app_know.conn.atlas.MongoClient")
    def test_context_manager_exception_still_disconnects(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        with self.assertRaises(RuntimeError):
            with AtlasClient(self.config) as client:
                raise RuntimeError("Test error")

        mock_client.close.assert_called_once()


class TestGetAtlasClient(TestCase):
    """Tests for get_atlas_client factory function."""

    @patch("app_know.conn.atlas.MongoClient")
    @patch.dict(os.environ, {
        "MONGO_ATLAS_USER": "factory_user",
        "MONGO_ATLAS_PASS": "factory_pass",
        "MONGO_ATLAS_HOST": "factory.mongodb.net",
    })
    def test_get_atlas_client_default(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = get_atlas_client()

        self.assertIsNotNone(client)
        self.assertTrue(client.is_connected())

    @patch("app_know.conn.atlas.MongoClient")
    @patch.dict(os.environ, {
        "MONGO_ATLAS_USER": "factory_user",
        "MONGO_ATLAS_PASS": "factory_pass",
        "MONGO_ATLAS_HOST": "factory.mongodb.net",
    })
    def test_get_atlas_client_with_db_name(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        client = get_atlas_client(db_name="custom_db")

        self.assertEqual(client.config.db_name, "custom_db")

    @patch("app_know.conn.atlas.MongoClient")
    @patch.dict(os.environ, {
        "MONGO_ATLAS_USER": "factory_user",
        "MONGO_ATLAS_PASS": "factory_pass",
        "MONGO_ATLAS_HOST": "factory.mongodb.net",
    })
    def test_get_atlas_client_with_timeout(self, mock_mongo_client):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        get_atlas_client(timeout_ms=15000)

        call_kwargs = mock_mongo_client.call_args[1]
        self.assertEqual(call_kwargs["serverSelectionTimeoutMS"], 15000)


def _make_mock_atlas_client():
    """Build a mock AtlasClient so tests never use real DNS/connection. Generated."""
    mock_client = MagicMock(spec=AtlasClient)
    mock_client.is_connected.return_value = True
    mock_client.ping.return_value = True
    mock_client.list_databases.return_value = ["admin", "local", "know"]
    mock_client.disconnect.return_value = None
    mock_coll = MagicMock()
    mock_coll.insert_one.return_value = MagicMock(inserted_id="mock_id_1")
    mock_coll.find_one.side_effect = lambda q: (
        {"_id": "mock_id_1", "name": "test_doc", "value": 456}
        if q.get("_id") == "mock_id_1"
        else None
    )
    mock_coll.update_one.return_value = MagicMock(modified_count=1)
    mock_coll.delete_one.return_value = MagicMock(deleted_count=1)
    mock_client.get_collection.return_value = mock_coll
    return mock_client


class TestAtlasClientIntegration(TestCase):
    """
    Integration-style tests for AtlasClient using a mock client only.
    No real MongoDB Atlas connection or DNS; all operations use mocks. Generated.
    """

    @patch("app_know.tests.test_atlas.get_atlas_client")
    def test_real_connection(self, mock_get_atlas):
        """Test connection behavior using mock (no real Atlas). Generated."""
        mock_client = _make_mock_atlas_client()
        mock_get_atlas.return_value = mock_client
        client = get_atlas_client(db_name="test", timeout_ms=10000)
        self.assertTrue(client.is_connected())
        self.assertTrue(client.ping())
        client.disconnect()
        mock_get_atlas.assert_called_once_with(db_name="test", timeout_ms=10000)

    @patch("app_know.tests.test_atlas.get_atlas_client")
    def test_real_list_databases(self, mock_get_atlas):
        """Test list_databases using mock (no real Atlas). Generated."""
        mock_client = _make_mock_atlas_client()
        mock_get_atlas.return_value = mock_client
        client = get_atlas_client(db_name="test", timeout_ms=10000)
        databases = client.list_databases()
        self.assertIsInstance(databases, list)
        self.assertIn("admin", databases)
        client.disconnect()

    @patch("app_know.tests.test_atlas.get_atlas_client")
    def test_real_crud_operations(self, mock_get_atlas):
        """Test CRUD operations using mock collection (no real Atlas). Generated."""
        mock_client = _make_mock_atlas_client()
        store = []

        def insert_one(doc):
            doc["_id"] = "mock_id_1"
            store.append(dict(doc))
            return MagicMock(inserted_id="mock_id_1")

        def find_one(query):
            for d in store:
                if d.get("_id") == query.get("_id"):
                    return dict(d)
            return None

        def update_one(filter_q, update):
            for d in store:
                if d.get("_id") == filter_q.get("_id") and "$set" in update:
                    d.update(update["$set"])
                    return MagicMock(modified_count=1)
            return MagicMock(modified_count=0)

        def delete_one(query):
            for i, d in enumerate(store):
                if d.get("_id") == query.get("_id"):
                    store.pop(i)
                    return MagicMock(deleted_count=1)
            return MagicMock(deleted_count=0)

        mock_coll = MagicMock()
        mock_coll.insert_one.side_effect = insert_one
        mock_coll.find_one.side_effect = find_one
        mock_coll.update_one.side_effect = update_one
        mock_coll.delete_one.side_effect = delete_one
        mock_client.get_collection.return_value = mock_coll
        mock_get_atlas.return_value = mock_client

        client = get_atlas_client(db_name="test", timeout_ms=10000)
        coll = client.get_collection("test_atlas_crud")
        doc = {"name": "test_doc", "value": 123}
        result = coll.insert_one(doc)
        self.assertIsNotNone(result.inserted_id)
        found = coll.find_one({"_id": result.inserted_id})
        self.assertEqual(found["name"], "test_doc")
        self.assertEqual(found["value"], 123)
        coll.update_one({"_id": result.inserted_id}, {"$set": {"value": 456}})
        updated = coll.find_one({"_id": result.inserted_id})
        self.assertEqual(updated["value"], 456)
        coll.delete_one({"_id": result.inserted_id})
        deleted = coll.find_one({"_id": result.inserted_id})
        self.assertIsNone(deleted)
        client.disconnect()
