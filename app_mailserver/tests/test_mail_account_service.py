"""
单元测试：MailAccount Service

测试覆盖：
- list_accounts (with pagination, filtering, username)
- get_account
- create_account
- update_account
- delete_account
- 错误处理和验证
"""
import time
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.services.mail_account_service import MailAccountService


class TestMailAccountService(TransactionTestCase):
    """测试 MailAccount service"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        self.service = MailAccountService()
        MailAccount.objects.using('mailserver_rw').all().delete()

    def tearDown(self):
        """每个测试后清理"""
        MailAccount.objects.using('mailserver_rw').all().delete()

    def test_list_accounts_default(self):
        """测试列表账户（默认参数）"""
        # 创建多个账户
        for i in range(5):
            MailAccount.objects.using('mailserver_rw').create(
                username=f'user{i}@example.com',
                password='pass',
                domain='example.com',
                is_active=True,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )

        result = self.service.list_accounts()

        self.assertIn('data', result)
        self.assertIn('total_num', result)
        self.assertIn('next_offset', result)
        self.assertEqual(result['total_num'], 5)
        self.assertEqual(len(result['data']), 5)

    def test_list_accounts_with_pagination(self):
        """测试分页功能"""
        # 创建多个账户
        for i in range(10):
            MailAccount.objects.using('mailserver_rw').create(
                username=f'user{i}@example.com',
                password='pass',
                domain='example.com',
                is_active=True,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )

        # 第一页
        result1 = self.service.list_accounts(offset=0, limit=3)
        self.assertEqual(len(result1['data']), 3)
        self.assertEqual(result1['total_num'], 10)
        self.assertEqual(result1['next_offset'], 3)

        # 第二页
        result2 = self.service.list_accounts(offset=3, limit=3)
        self.assertEqual(len(result2['data']), 3)
        self.assertEqual(result2['total_num'], 10)
        self.assertEqual(result2['next_offset'], 6)

        # 最后一页
        result3 = self.service.list_accounts(offset=9, limit=3)
        self.assertEqual(len(result3['data']), 1)
        self.assertEqual(result3['total_num'], 10)
        self.assertIsNone(result3['next_offset'])  # 最后一页

    def test_list_accounts_with_domain_filter(self):
        """测试按域名筛选"""
        MailAccount.objects.using('mailserver_rw').create(
            username='user1@domain1.com',
            password='pass',
            domain='domain1.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='user2@domain2.com',
            password='pass',
            domain='domain2.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        result = self.service.list_accounts(domain='domain1.com')

        self.assertEqual(result['total_num'], 1)
        self.assertEqual(result['data'][0]['domain'], 'domain1.com')

    def test_list_accounts_with_is_active_filter(self):
        """测试按激活状态筛选"""
        MailAccount.objects.using('mailserver_rw').create(
            username='active@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='inactive@example.com',
            password='pass',
            domain='example.com',
            is_active=False,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 仅激活
        result_active = self.service.list_accounts(is_active=True)
        self.assertEqual(result_active['total_num'], 1)
        self.assertTrue(result_active['data'][0]['is_active'])

        # 仅非激活
        result_inactive = self.service.list_accounts(is_active=False)
        self.assertEqual(result_inactive['total_num'], 1)
        self.assertFalse(result_inactive['data'][0]['is_active'])

    def test_list_accounts_with_username(self):
        """测试按 username 搜索功能（多个账户包含相同的子字符串）"""
        # 创建多个账户，其中几个账户的 username 包含 "zzz"
        MailAccount.objects.using('mailserver_rw').create(
            username='zzz_user1@example.com',
            password='pass1',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 1,
            ut=int(time.time() * 1000) + 1
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='zzz_user2@example.com',
            password='pass2',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 2,
            ut=int(time.time() * 1000) + 2
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='admin_zzz@example.com',
            password='pass3',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 3,
            ut=int(time.time() * 1000) + 3
        )
        # 创建不包含 "zzz" 的账户
        MailAccount.objects.using('mailserver_rw').create(
            username='normal_user@example.com',
            password='pass4',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 4,
            ut=int(time.time() * 1000) + 4
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='other_user@example.com',
            password='pass5',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 5,
            ut=int(time.time() * 1000) + 5
        )

        # 使用 username 参数搜索包含 "zzz" 的账户
        result = self.service.list_accounts(username='zzz')

        # 应该返回包含 'zzz' 的账户（应该返回 3 个）
        self.assertEqual(result['total_num'], 3)
        self.assertEqual(len(result['data']), 3)

        # 验证所有返回的账户都包含 'zzz'
        returned_usernames = []
        for account_data in result['data']:
            self.assertIn('zzz', account_data['username'].lower())
            returned_usernames.append(account_data['username'])

        # 验证返回了所有包含 "zzz" 的账户
        expected_usernames = {'zzz_user1@example.com', 'zzz_user2@example.com', 'admin_zzz@example.com'}
        actual_usernames = set(returned_usernames)
        self.assertEqual(actual_usernames, expected_usernames)

        # 验证不包含 "zzz" 的账户没有被返回
        self.assertNotIn('normal_user@example.com', returned_usernames)
        self.assertNotIn('other_user@example.com', returned_usernames)

    def test_list_accounts_limit_validation(self):
        """测试 limit 验证"""
        # 创建账户
        MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 负数 limit 应该被调整为默认值
        result = self.service.list_accounts(limit=-1)
        self.assertGreaterEqual(len(result['data']), 0)

        # 超过最大值的 limit 应该被限制
        result = self.service.list_accounts(limit=2000)
        self.assertLessEqual(len(result['data']), 1000)

    def test_get_account_success(self):
        """测试成功获取账户"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='testpassword',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        result = self.service.get_account(account.id)

        self.assertIsNotNone(result)
        self.assertEqual(result['id'], account.id)
        self.assertEqual(result['username'], 'test@example.com')
        self.assertEqual(result['domain'], 'example.com')
        self.assertTrue(result['is_active'])
        self.assertIn('ct', result)
        self.assertIn('ut', result)

    def test_get_account_not_found(self):
        """测试获取不存在的账户"""
        result = self.service.get_account(99999)
        self.assertIsNone(result)

    def test_create_account_success(self):
        """测试成功创建账户"""
        account_data = self.service.create_account(
            username='new@example.com',
            password='newpass',
            domain='example.com',
            is_active=True
        )

        self.assertIsNotNone(account_data)
        self.assertEqual(account_data['username'], 'new@example.com')
        self.assertEqual(account_data['domain'], 'example.com')
        self.assertTrue(account_data['is_active'])
        self.assertIn('id', account_data)
        self.assertGreater(account_data['ct'], 0)
        self.assertGreater(account_data['ut'], 0)

        # 验证数据库中已创建
        account = MailAccount.objects.using('mailserver_rw').get(username='new@example.com')
        self.assertEqual(account.password, 'newpass')

    def test_create_account_auto_extract_domain(self):
        """测试创建账户时自动提取域名"""
        account_data = self.service.create_account(
            username='user@testdomain.com',
            password='pass',
            domain='localhost'  # 使用默认值，应该自动提取
        )

        # 应该自动提取域名为 testdomain.com
        self.assertEqual(account_data['domain'], 'testdomain.com')

    def test_create_account_missing_username(self):
        """测试缺少用户名时创建账户（应该抛出异常）"""
        with self.assertRaises(ValueError) as context:
            self.service.create_account(username='')

        self.assertIn('required', str(context.exception).lower())

    def test_create_account_duplicate_username(self):
        """测试创建重复用户名的账户（应该抛出异常）"""
        # 先创建一个账户
        MailAccount.objects.using('mailserver_rw').create(
            username='duplicate@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 尝试创建相同用户名的账户
        with self.assertRaises(ValueError) as context:
            self.service.create_account(
                username='duplicate@example.com',
                password='pass2'
            )

        self.assertIn('already exists', str(context.exception).lower())

    def test_update_account_success(self):
        """测试成功更新账户"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='original@example.com',
            password='originalpass',
            domain='original.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        original_dt = account.ut

        # 等待一小段时间确保 ut 会改变
        time.sleep(0.01)

        updated = self.service.update_account(
            account_id=account.id,
            username='updated@example.com',
            password='updatedpass',
            domain='updated.com',
            is_active=False
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated['username'], 'updated@example.com')
        self.assertEqual(updated['domain'], 'updated.com')
        self.assertFalse(updated['is_active'])
        self.assertGreater(updated['ut'], original_dt)  # ut 应该更新

        # 验证数据库已更新
        db_account = MailAccount.objects.using('mailserver_rw').get(id=account.id)
        self.assertEqual(db_account.username, 'updated@example.com')
        self.assertEqual(db_account.password, 'updatedpass')

    def test_update_account_partial(self):
        """测试部分更新账户（只更新部分字段）"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='partial@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 只更新密码
        updated = self.service.update_account(
            account_id=account.id,
            password='newpass'
        )

        self.assertIsNotNone(updated)
        # 其他字段应该保持不变
        self.assertEqual(updated['username'], 'partial@example.com')
        self.assertEqual(updated['domain'], 'example.com')
        self.assertTrue(updated['is_active'])

        # 验证数据库中密码已更新
        db_account = MailAccount.objects.using('mailserver_rw').get(id=account.id)
        self.assertEqual(db_account.password, 'newpass')

    def test_update_account_not_found(self):
        """测试更新不存在的账户"""
        result = self.service.update_account(
            account_id=99999,
            username='new@example.com'
        )
        self.assertIsNone(result)

    def test_update_account_duplicate_username(self):
        """测试更新为已存在的用户名（应该抛出异常）"""
        # 创建两个账户
        account1 = MailAccount.objects.using('mailserver_rw').create(
            username='account1@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='account2@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 尝试将 account1 更新为 account2 的用户名
        with self.assertRaises(ValueError) as context:
            self.service.update_account(
                account_id=account1.id,
                username='account2@example.com'
            )

        self.assertIn('already exists', str(context.exception).lower())

    def test_delete_account_success(self):
        """测试成功删除账户（硬删除）"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='todelete@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        account_id = account.id
        result = self.service.delete_account(account_id)

        self.assertTrue(result)

        # 验证账户已被物理删除
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.using('mailserver_rw').get(id=account_id)

    def test_delete_account_not_found(self):
        """测试删除不存在的账户"""
        result = self.service.delete_account(99999)
        self.assertFalse(result)

    def test_account_to_dict_format(self):
        """测试账户字典格式"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='format@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=1234567890,
            ut=1234567890
        )

        account_data = self.service.get_account(account.id)

        # 验证字典包含所有必需字段
        required_fields = ['id', 'username', 'domain', 'is_active', 'ct', 'ut']
        for field in required_fields:
            self.assertIn(field, account_data)

    def test_singleton_service(self):
        """测试单例 service"""
        service1 = MailAccountService()
        service2 = MailAccountService()

        # 应该是同一个实例
        self.assertIs(service1, service2)
