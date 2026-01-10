"""测试 SnowflakeGenerator，使用 TransactionTestCase 以支持真正的数据库操作"""

import time
from django.db import transaction
from django.test import TransactionTestCase

from app_snowflake.consts.snowflake_const import (
    MASK_DATACENTER_ID, MASK_MACHINE_ID, MASK_BUSINESS_ID,
    MASK_SEQUENCE, CLOCK_BACKWARD_THRESHOLD
)
from app_snowflake.models.recounter import Recounter
from app_snowflake.services.snowflake_generator import SnowflakeGenerator


class TestSnowflakeGenerator(TransactionTestCase):
    """测试 SnowflakeGenerator，使用 TransactionTestCase 以支持真正的事务测试和数据库操作"""

    databases = {'default', 'snowflake_rw'}

    def setUp(self):
        """每个测试前清理数据"""
        # 设置测试用的 datacenter_id 和 machine_id
        self.datacenter_id = 1
        self.machine_id = 2
        self.business_id = 3
        # 使用当前时间作为起始时间戳
        self.start_timestamp = int(time.time() * 1000)

        # 清理测试数据
        Recounter.objects.using('snowflake_rw').filter(dcid=self.datacenter_id, mid=self.machine_id).delete()

    def tearDown(self):
        """每个测试后清理数据"""
        Recounter.objects.using('snowflake_rw').filter(
            dcid=self.datacenter_id,
            mid=self.machine_id
        ).delete()

    def test_init_with_valid_parameters(self):
        """测试使用有效参数初始化"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        self.assertEqual(generator.datacenter_id, self.datacenter_id)
        self.assertEqual(generator.machine_id, self.machine_id)
        self.assertEqual(generator.start_timestamp, self.start_timestamp)
        self.assertEqual(generator.sequence, 0)
        self.assertEqual(generator.last_timestamp, -1)

        # 验证数据库中有记录被创建（通过 recount 调用）
        recounter = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertIsNotNone(recounter)

    def test_init_with_invalid_datacenter_id(self):
        """测试使用无效的 datacenter_id 初始化"""
        with self.assertRaises(ValueError) as context:
            SnowflakeGenerator(
                datacenter_id=MASK_DATACENTER_ID + 1,
                machine_id=self.machine_id,

                start_timestamp=self.start_timestamp
            )
        self.assertIn("datacenter_id", str(context.exception))

    def test_init_with_invalid_machine_id(self):
        """测试使用无效的 machine_id 初始化"""
        with self.assertRaises(ValueError) as context:
            SnowflakeGenerator(
                datacenter_id=self.datacenter_id,
                machine_id=MASK_MACHINE_ID + 1,

                start_timestamp=self.start_timestamp
            )
        self.assertIn("machine_id", str(context.exception))

    def test_generate_single_id(self):
        """测试生成单个ID"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        id_value = generator.generate(self.business_id)

        # 验证ID是正数
        self.assertGreater(id_value, 0)

        # 验证ID可以被解析
        parsed = generator.parse_id(id_value)
        self.assertEqual(parsed['datacenter_id'], self.datacenter_id)
        self.assertEqual(parsed['machine_id'], self.machine_id)
        self.assertEqual(parsed['business_id'], self.business_id)
        self.assertGreaterEqual(parsed['timestamp'], self.start_timestamp)

        # 验证数据库中有记录（通过 recount 调用）
        recounter = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertIsNotNone(recounter)

    def test_generate_multiple_ids_are_unique(self):
        """测试生成多个ID，验证它们都是唯一的"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        ids = generator.generate_batch(self.business_id, 10)

        # 验证所有ID都是唯一的
        self.assertEqual(len(ids), len(set(ids)))

        # 验证所有ID都是正数
        for id_value in ids:
            self.assertGreater(id_value, 0)

    def test_generate_batch(self):
        """测试批量生成ID"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        count = 5
        ids = generator.generate_batch(self.business_id, count)

        self.assertEqual(len(ids), count)

        # 验证每个ID都可以被正确解析
        for id_value in ids:
            parsed = generator.parse_id(id_value)
            self.assertEqual(parsed['datacenter_id'], self.datacenter_id)
            self.assertEqual(parsed['machine_id'], self.machine_id)
            self.assertEqual(parsed['business_id'], self.business_id)

    def test_parse_id(self):
        """测试解析ID"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        id_value = generator.generate(self.business_id)
        parsed = generator.parse_id(id_value)

        # 验证解析结果包含所有必要的字段
        self.assertIn('timestamp', parsed)
        self.assertIn('datacenter_id', parsed)
        self.assertIn('machine_id', parsed)
        self.assertIn('recount', parsed)
        self.assertIn('business_id', parsed)
        self.assertIn('sequence', parsed)

        # 验证解析的值与生成器配置一致
        self.assertEqual(parsed['datacenter_id'], self.datacenter_id)
        self.assertEqual(parsed['machine_id'], self.machine_id)
        self.assertEqual(parsed['business_id'], self.business_id)

        # 验证时间戳合理
        current_time = int(time.time() * 1000)
        self.assertGreaterEqual(parsed['timestamp'], self.start_timestamp)
        self.assertLessEqual(parsed['timestamp'], current_time + 1000)  # 允许1秒误差

    def test_sequence_increment_within_same_millisecond(self):
        """测试在同一毫秒内序列号递增"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        # 生成第一个ID
        id1 = generator.generate(self.business_id)
        parsed1 = generator.parse_id(id1)

        # 快速生成第二个ID（可能在同一毫秒内）
        id2 = generator.generate(self.business_id)
        parsed2 = generator.parse_id(id2)

        # 如果时间戳相同，序列号应该递增
        if parsed1['timestamp'] == parsed2['timestamp']:
            self.assertGreater(parsed2['sequence'], parsed1['sequence'])
        else:
            # 如果时间戳不同，序列号应该重置为0
            self.assertEqual(parsed2['sequence'], 0)

    def test_restart_scenario(self):
        """测试重启场景（last_timestamp == -1）"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 第一次生成（重启场景）
        id1 = generator.generate(self.business_id)
        parsed1 = generator.parse_id(id1)
        self.assertEqual(parsed1.get("datacenter_id"), self.datacenter_id)
        self.assertEqual(parsed1.get("machine_id"), self.machine_id)
        self.assertEqual(parsed1.get("business_id"), self.business_id)
        self.assertGreaterEqual(parsed1.get("timestamp"), self.start_timestamp)
        self.assertEqual(parsed1.get("sequence"), 0)

        # 记录第一次的 recounter 值
        recounter1 = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        initial_rc = recounter1.rc

        # 模拟重启：清除 Singleton 缓存，然后创建新的生成器实例
        # __init__ 会调用一次 recount()
        # 清除该类的所有缓存实例，以便重新创建
        # Singleton 的 _instances 存储在元类上，格式为 _instances[clazz][args_hash] = instance
        # 通过元类访问 _instances
        metaclass = type(SnowflakeGenerator)
        if hasattr(metaclass, '_instances'):
            instances_dict = getattr(metaclass, '_instances')
            if SnowflakeGenerator in instances_dict:
                instances_dict[SnowflakeGenerator].clear()
        generator2 = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,

            start_timestamp=self.start_timestamp
        )

        # 验证 __init__ 后 recounter 已更新（真正操作数据库）
        recounter_after_init = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        expected_rc_after_init = (initial_rc + 1) & 3  # MASK_RECOUNT = 3
        self.assertEqual(recounter_after_init.rc, expected_rc_after_init,
                         "第二个生成器 __init__ 后 recounter 应该递增")

        # 第二次生成（应该触发 recount，因为 last_timestamp == -1）
        id2 = generator2.generate(self.business_id)
        parsed2 = generator2.parse_id(id2)
        self.assertEqual(parsed2.get("datacenter_id"), self.datacenter_id)
        self.assertEqual(parsed2.get("machine_id"), self.machine_id)
        self.assertEqual(parsed2.get("business_id"), self.business_id)
        self.assertGreaterEqual(parsed2.get("timestamp"), self.start_timestamp)
        self.assertEqual(parsed2.get("sequence"), 0)

        # 验证 generate(self.business_id) 后 recounter 值已更新（真正操作数据库）
        # __init__ 调用一次 recount，generate(self.business_id) 再调用一次 recount，所以总共递增 2 次
        recounter2 = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        expected_rc = (initial_rc + 2) & 3  # MASK_RECOUNT = 3
        self.assertEqual(recounter2.rc, expected_rc,
                         "第二个生成器 generate(self.business_id) 后 recounter 应该再递增一次")

    def test_clock_backward_within_threshold(self):
        """测试时钟回退但在阈值内的情况"""
        from unittest.mock import patch

        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 生成第一个ID
        generator.generate(self.business_id)

        # 模拟时钟回退（在阈值内）
        original_timestamp = generator.last_timestamp
        # 模拟当前时间回退到稍早的时间（在阈值内）
        backward_timestamp = original_timestamp - CLOCK_BACKWARD_THRESHOLD + 1
        # 等待后的时间戳应该大于 original_timestamp
        recovered_timestamp = original_timestamp + 1

        # Mock _current_timestamp 返回回退的时间（用于检测时钟回退）
        # Mock _wait_next_millis 返回恢复后的时间（模拟等待时钟恢复）
        with patch.object(generator, '_current_timestamp', return_value=backward_timestamp), \
                patch.object(generator, '_wait_next_millis', return_value=recovered_timestamp):
            # 应该能够正常生成ID（等待时钟恢复）
            id_value = generator.generate(self.business_id)
            self.assertGreater(id_value, 0)

        # 验证时间戳已更新（应该等待到至少 original_timestamp）
        self.assertGreaterEqual(generator.last_timestamp, original_timestamp)

    def test_clock_backward_beyond_threshold(self):
        """测试时钟回退超过阈值的情况"""
        from unittest.mock import patch

        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 生成第一个ID
        generator.generate(self.business_id)

        # 记录初始 recounter 值
        recounter1 = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        initial_rc = recounter1.rc

        # 模拟时钟回退（超过阈值）
        # last_timestamp 是之前的时间戳，当前时间应该更早
        original_timestamp = generator.last_timestamp
        # 模拟当前时间回退到更早的时间（超过阈值）
        backward_timestamp = original_timestamp - CLOCK_BACKWARD_THRESHOLD - 1

        # Mock _current_timestamp 返回回退后的时间
        with patch.object(generator, '_current_timestamp', return_value=backward_timestamp):
            # 应该触发 recount（真正操作数据库）
            id_value = generator.generate(self.business_id)
            self.assertGreater(id_value, 0)

        # 验证 recounter 值已更新（真正操作数据库）
        recounter2 = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        expected_rc = (initial_rc + 1) & 3  # MASK_RECOUNT = 3
        self.assertEqual(recounter2.rc, expected_rc)

    def test_sequence_overflow(self):
        """测试序列号溢出场景"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 设置序列号为最大值
        generator.sequence = MASK_SEQUENCE
        generator.last_timestamp = generator._current_timestamp()

        # 生成ID，应该等待下一毫秒
        id_value = generator.generate(self.business_id)
        self.assertGreater(id_value, 0)

        # 验证序列号已重置
        parsed = generator.parse_id(id_value)
        self.assertEqual(parsed['sequence'], 0)

    def test_database_transaction_consistency(self):
        """测试数据库事务一致性"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 在一个事务中生成ID
        with transaction.atomic():
            id_value = generator.generate(self.business_id)

            # 验证数据库中有记录
            recounter = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
            self.assertIsNotNone(recounter)

            # 验证ID可以解析
            parsed = generator.parse_id(id_value)
            self.assertEqual(parsed['datacenter_id'], self.datacenter_id)

    def test_concurrent_generation(self):
        """测试并发生成ID（多线程）"""
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        import threading

        ids = []
        lock = threading.Lock()

        def generate_id():
            id_value = generator.generate(self.business_id)
            with lock:
                ids.append(id_value)

        # 创建多个线程并发生成ID
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=generate_id)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有ID都是唯一的
        self.assertEqual(len(ids), len(set(ids)))

        # 验证数据库中有记录（真正操作数据库）
        recounter = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertIsNotNone(recounter)

    def test_different_datacenter_machine_ids(self):
        """测试不同的 datacenter_id 和 machine_id 组合"""
        # 测试多个不同的组合
        test_cases = [
            (0, 0, 0),
            (1, 1, 1),
            (MASK_DATACENTER_ID, MASK_MACHINE_ID, MASK_BUSINESS_ID),
        ]

        for dcid, mid, bid in test_cases:
            # 清理数据
            Recounter.objects.using('snowflake_rw').filter(dcid=dcid, mid=mid).delete()

            generator = SnowflakeGenerator(
                datacenter_id=dcid,
                machine_id=mid,
                start_timestamp=self.start_timestamp
            )

            id_value = generator.generate(bid)
            parsed = generator.parse_id(id_value)

            self.assertEqual(parsed['datacenter_id'], dcid)
            self.assertEqual(parsed['machine_id'], mid)
            self.assertEqual(parsed['business_id'], bid)

            # 验证数据库中有对应的记录（真正操作数据库）
            recounter = Recounter.objects.using('snowflake_rw').get(dcid=dcid, mid=mid)
            self.assertIsNotNone(recounter)

            # 清理
            Recounter.objects.using('snowflake_rw').filter(dcid=dcid, mid=mid).delete()

    def test_recounter_wraps_around(self):
        """测试 recounter 回绕（从3回到0）"""
        # 创建初始记录，rc=3
        Recounter.objects.using('snowflake_rw').create(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=3,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 创建生成器时，__init__ 会调用 recount，rc 应该从 3 回绕到 0
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp
        )

        # 验证 __init__ 后数据库中的 recounter 值已回绕（真正操作数据库）
        recounter_after_init = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter_after_init.rc, 0, "recounter 应该从 3 回绕到 0")

        # 生成ID，由于 last_timestamp == -1，会再次调用 recount，rc 应该从 0 变为 1
        id_value = generator.generate(self.business_id)
        self.assertGreater(id_value, 0)

        # 验证 generate(self.business_id) 后数据库中的 recounter 值（真正操作数据库）
        recounter_after_generate = Recounter.objects.using('snowflake_rw').get(dcid=self.datacenter_id, mid=self.machine_id)
        self.assertEqual(recounter_after_generate.rc, 1, "generate(self.business_id) 后 recounter 应该从 0 变为 1")
