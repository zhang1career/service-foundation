from unittest import TestCase

from common.drivers.neo4j_driver import Neo4jDriver


class TestNeo4jDriver(TestCase):
    def setUp(self):
        self.dut = Neo4jDriver('bolt://34.203.240.142:7474', 'neo4j', '9TRagjq8SGPDvhV')

    def test_run(self):
        # 测试连接
        try:
            self.dut.run("MATCH (n) RETURN n LIMIT 1")
        except Exception as e:
            print(f"Connection failed: {e}")

    def test_create_node(self):
        # 测试创建节点
        node = self.dut.create_node("Person", {"name": "Alice", "age": 30})
        self.assertIsNotNone(node)

    def test_create_edge(self):
        # 测试创建关系
        start_node = self.dut.create_node("company", {"name": "Alice"})
        end_node = self.dut.create_node("Person", {"name": "Bob"})
        edge = self.dut.create_edge(start_node, end_node, "KNOWS")
        self.assertIsNotNone(edge)

    def test_find_node_list(self):
        # 测试批量查询
        node_list = self.dut.find_node_list("idnex")
        self.assertIsNotNone(node_list)

    def test_find_an_edge(self):
        # 测试查找关系
        start_node = self.dut.find_node("company", {"name": "google"})
        end_node = self.dut.find_node("business", {"name": "internet advertising"})
        found_edge = self.dut.find_an_edge(start_node, end_node, "BELONG_TO")
        self.assertIsNotNone(found_edge)

    def test_find_src_list_from_dest(self):
        # 测试查找源节点列表
        dest_node = self.dut.find_node("business", {"name": "internet advertising"})
        src_list = self.dut.find_src_list_from_dest(dest_node, "BELONG_TO")
        self.assertIsNotNone(src_list)
        print(src_list)

    def test_find_dest_list_from_src(self):
        # 测试查找宿节点列表
        start_node = self.dut.find_node("company", {"name": "google"})
        dest_list = self.dut.find_dest_list_from_src(start_node, "BELONG_TO")
        self.assertIsNotNone(dest_list)
        print(dest_list)


    def test_delete_node(self):
        # 测试删除节点
        found_node = self.dut.find_node("index", {"name": "number of jobs"})
        self.dut.delete_node(found_node)


    def test_delete_edge(self):
        # 测试删除关系
        start_node = self.dut.find_node("news", {"name": "market capitalization"})
        end_node = self.dut.find_node("concept", {"name": "name: market capitalization"})
        edge = self.dut.find_an_edge(start_node, end_node, "CORRELATE")
        self.dut.delete_edge(edge)


    def test_delete_all(self):
        # 测试删除所有节点和关系
        self.dut.delete_all()
