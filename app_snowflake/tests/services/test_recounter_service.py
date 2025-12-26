from django.db import transaction
from django.test import TransactionTestCase

from app_snowflake.models.recounter import Recounter
from app_snowflake.services.recounter_service import create_or_update_recount, get_recounter


class TestRecounterService(TransactionTestCase):
    """测试 recounter_service，使用 TransactionTestCase 以支持真正的事务测试和数据库操作"""

    def setUp(self):
        """每个测试前清理数据"""
        # 设置测试用的 datacenter_id 和 machine_id
        self.datacenter_id = 999
        self.machine_id = 888
        # 清理测试数据
        Recounter.objects.filter(dcid=self.datacenter_id, mid=self.machine_id).delete()

    def tearDown(self):
        """每个测试后清理数据"""
        Recounter.objects.filter(
            dcid=self.datacenter_id,
            mid=self.machine_id
        ).delete()

    def test_recount_update_existing_record(self):
        """测试更新现有记录的情况"""
        # 先创建一条记录
        initial_count = 0
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=initial_count,
            ct=1234567890000,
            ut=1234567890000
        )

        # 调用 recount，应该递增计数器
        result = create_or_update_recount(self.datacenter_id, self.machine_id)

        # 验证返回值应该是 (0 + 1) % 4 = 1
        self.assertEqual(result, 1)

        # 验证数据库中的值已经更新（真正操作数据库）
        recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter.rc, 1)
        self.assertEqual(recounter.dcid, self.datacenter_id)
        self.assertEqual(recounter.mid, self.machine_id)

    def test_recount_counter_wraps_around(self):
        """测试计数器在 4 时回绕到 0"""
        # 创建一条 rc=3 的记录
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=3,
            ct=1234567890000,
            ut=1234567890000
        )

        # 调用 recount，应该是 (3 + 1) % 4 = 0
        result = create_or_update_recount(self.datacenter_id, self.machine_id)
        self.assertEqual(result, 0)

        # 验证数据库中的值（真正操作数据库）
        recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter.rc, 0)

    def test_recount_transaction_rollback_on_exception(self):
        """测试事务回滚：当在事务中抛出异常时，数据应该回滚"""
        # 先创建一个记录
        initial_count = 1
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=initial_count,
            ct=1234567890000,
            ut=1234567890000
        )

        # 记录原始值
        original_recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        original_rc = original_recounter.rc
        original_ut = original_recounter.ut

        # 在一个会抛出异常的事务中调用 recount
        try:
            with transaction.atomic():
                # 调用 recount 更新计数器
                create_or_update_recount(self.datacenter_id, self.machine_id)
                # 故意抛出异常，触发回滚
                raise ValueError("Test exception to trigger rollback")
        except ValueError:
            pass  # 捕获异常，继续测试

        # 验证事务回滚：数据库中的值应该没有改变（真正验证数据库状态）
        recounter_after_rollback = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter_after_rollback.rc, original_rc,
                         "事务回滚后，rc 应该保持原始值")
        self.assertEqual(recounter_after_rollback.ut, original_ut,
                         "事务回滚后，ut 应该保持原始值")

    def test_recount_transaction_commit_on_success(self):
        """测试事务提交：正常执行时，数据应该被提交到数据库"""
        # 创建初始记录
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=2,
            ct=1234567890000,
            ut=1234567890000
        )

        # 在一个事务中调用 recount，但不抛出异常
        with transaction.atomic():
            result = create_or_update_recount(self.datacenter_id, self.machine_id)

        # 验证事务提交：数据应该已经更新（真正操作数据库）
        recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter.rc, (2 + 1) % 4)  # 应该是 3
        self.assertEqual(result, 3)

    def test_recount_multiple_calls_in_sequence(self):
        """测试连续多次调用 recount，验证每次都能正确更新数据库"""
        # 创建初始记录
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=0,
            ct=1234567890000,
            ut=1234567890000
        )

        # 连续调用多次，每次都真正操作数据库
        results = []
        for i in range(5):
            result = create_or_update_recount(self.datacenter_id, self.machine_id)
            results.append(result)
            # 每次调用后验证数据库状态
            recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
            self.assertEqual(recounter.rc, result)

        # 验证结果序列：0 -> 1 -> 2 -> 3 -> 0 (因为回绕)
        expected_results = [1, 2, 3, 0, 1]
        self.assertEqual(results, expected_results)

        # 验证最终数据库中的值
        recounter = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter.rc, 1)

    def test_recount_transaction_isolation(self):
        """测试事务隔离：两个连续事务应该正确提交"""
        # 创建初始记录
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=0,
            ct=1234567890000,
            ut=1234567890000
        )

        # 第一个事务：正常执行
        with transaction.atomic():
            result1 = create_or_update_recount(self.datacenter_id, self.machine_id)

        # 验证第一个事务提交后的值（真正操作数据库）
        recounter1 = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter1.rc, 1)
        self.assertEqual(result1, 1)

        # 第二个事务：正常执行
        with transaction.atomic():
            result2 = create_or_update_recount(self.datacenter_id, self.machine_id)

        # 验证第二个事务提交后的值（真正操作数据库）
        recounter2 = Recounter.objects.get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter2.rc, 2)
        self.assertEqual(result2, 2)

    def test_get_recount_raises_exception_for_non_existent(self):
        """测试 get_recount 对于不存在的记录不会抛出异常"""
        # 注意：get_recount 内部调用 get_recounter，get_recounter 使用 objects.get()
        result = get_recounter(self.datacenter_id, self.machine_id)
        self.assertIsNone(result)

    def test_get_recount_returns_existing_value(self):
        """测试 get_recount 返回现有记录的值"""
        # 创建记录
        Recounter.objects.create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=2,
            ct=1234567890000,
            ut=1234567890000
        )

        result = get_recounter(self.datacenter_id, self.machine_id)
        self.assertEqual(result, 2)
