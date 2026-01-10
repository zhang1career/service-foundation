"""
单元测试：MailAccount Repository

测试覆盖：
- get_account_by_id
- get_account_by_username
- get_account_by_username_any
- list_accounts (with pagination, filtering, search)
- create_account
- update_account
- delete_account (hard delete)
"""
import time
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.repos.mail_account_repo import (
    get_account_by_id,
    get_account_by_username,
    get_account_by_username_any,
    list_accounts,
    create_account,
    update_account,
    delete_account,
)


class TestMailAccountRepo(TransactionTestCase):
    """测试 MailAccount repository 函数"""
    
    databases = {'default', 'mailserver_rw'}
    
    def setUp(self):
        """每个测试前清理数据"""
        MailAccount.objects.using('mailserver_rw').all().delete()
    
    def tearDown(self):
        """每个测试后清理数据"""
        MailAccount.objects.using('mailserver_rw').all().delete()
    
    def test_get_account_by_id_success(self):
        """测试根据 ID 获取账户成功"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = get_account_by_id(account.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, account.id)
        self.assertEqual(result.username, 'test@example.com')
    
    def test_get_account_by_id_not_found(self):
        """测试根据 ID 获取不存在的账户"""
        result = get_account_by_id(99999)
        self.assertIsNone(result)
    
    def test_get_account_by_username_success(self):
        """测试根据用户名获取账户（仅激活）"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='active@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = get_account_by_username('active@example.com', is_active=True)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.username, 'active@example.com')
        self.assertTrue(result.is_active)
    
    def test_get_account_by_username_inactive_filtered(self):
        """测试根据用户名获取账户时过滤非激活账户"""
        MailAccount.objects.using('mailserver_rw').create(
            username='inactive@example.com',
            password='pass',
            domain='example.com',
            is_active=False,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = get_account_by_username('inactive@example.com', is_active=True)
        self.assertIsNone(result)  # 应该被过滤掉
    
    def test_get_account_by_username_any_success(self):
        """测试根据用户名获取账户（任意状态）"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='any@example.com',
            password='pass',
            domain='example.com',
            is_active=False,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = get_account_by_username_any('any@example.com')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.username, 'any@example.com')
        self.assertFalse(result.is_active)  # 应该能获取非激活账户
    
    def test_list_accounts_default(self):
        """测试列表账户（默认参数）"""
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
        
        result = list_accounts()
        
        self.assertIn('accounts', result)
        self.assertIn('total', result)
        self.assertEqual(result['total'], 10)
        self.assertEqual(len(result['accounts']), 10)  # 默认 limit=20
    
    def test_list_accounts_with_pagination(self):
        """测试列表账户（分页）"""
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
        result1 = list_accounts(offset=0, limit=3)
        self.assertEqual(len(result1['accounts']), 3)
        self.assertEqual(result1['total'], 10)
        
        # 第二页
        result2 = list_accounts(offset=3, limit=3)
        self.assertEqual(len(result2['accounts']), 3)
        self.assertEqual(result2['total'], 10)
        
        # 验证不同页的数据不同
        self.assertNotEqual(result1['accounts'][0].id, result2['accounts'][0].id)
    
    def test_list_accounts_with_domain_filter(self):
        """测试列表账户（按域名筛选）"""
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
        
        result = list_accounts(domain='domain1.com')
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['accounts'][0].domain, 'domain1.com')
    
    def test_list_accounts_with_is_active_filter(self):
        """测试列表账户（按激活状态筛选）"""
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
        result_active = list_accounts(is_active=True)
        self.assertEqual(result_active['total'], 1)
        self.assertTrue(result_active['accounts'][0].is_active)
        
        # 仅非激活
        result_inactive = list_accounts(is_active=False)
        self.assertEqual(result_inactive['total'], 1)
        self.assertFalse(result_inactive['accounts'][0].is_active)
    
    def test_list_accounts_with_search(self):
        """测试列表账户（搜索）"""
        MailAccount.objects.using('mailserver_rw').create(
            username='alice@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        MailAccount.objects.using('mailserver_rw').create(
            username='bob@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = list_accounts(search='alice')
        
        self.assertEqual(result['total'], 1)
        self.assertIn('alice', result['accounts'][0].username.lower())
    
    def test_create_account_success(self):
        """测试创建账户成功"""
        account = create_account(
            username='new@example.com',
            password='newpass',
            domain='example.com',
            is_active=True
        )
        
        self.assertIsNotNone(account)
        self.assertEqual(account.username, 'new@example.com')
        self.assertEqual(account.password, 'newpass')
        self.assertEqual(account.domain, 'example.com')
        self.assertTrue(account.is_active)
        self.assertGreater(account.ct, 0)
        self.assertGreater(account.ut, 0)
        
        # 验证数据库中已创建
        db_account = MailAccount.objects.using('mailserver_rw').get(username='new@example.com')
        self.assertEqual(db_account.id, account.id)
    
    def test_create_account_auto_extract_domain(self):
        """测试创建账户时自动提取域名"""
        account = create_account(
            username='user@testdomain.com',
            password='pass',
            domain='localhost'  # 使用默认值
        )
        
        # 应该自动提取域名为 testdomain.com
        self.assertEqual(account.domain, 'testdomain.com')
    
    def test_update_account_success(self):
        """测试更新账户成功"""
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
        
        updated = update_account(
            account_id=account.id,
            username='updated@example.com',
            password='updatedpass',
            domain='updated.com',
            is_active=False
        )
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated.username, 'updated@example.com')
        self.assertEqual(updated.password, 'updatedpass')
        self.assertEqual(updated.domain, 'updated.com')
        self.assertFalse(updated.is_active)
        self.assertGreater(updated.ut, original_dt)  # ut 应该更新
        
        # 验证数据库已更新
        db_account = MailAccount.objects.using('mailserver_rw').get(id=account.id)
        self.assertEqual(db_account.username, 'updated@example.com')
    
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
        updated = update_account(
            account_id=account.id,
            password='newpass'
        )
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated.password, 'newpass')
        # 其他字段应该保持不变
        self.assertEqual(updated.username, 'partial@example.com')
        self.assertEqual(updated.domain, 'example.com')
        self.assertTrue(updated.is_active)
    
    def test_update_account_not_found(self):
        """测试更新不存在的账户"""
        result = update_account(
            account_id=99999,
            username='new@example.com'
        )
        self.assertIsNone(result)
    
    def test_delete_account_success(self):
        """测试删除账户成功（硬删除）"""
        account = MailAccount.objects.using('mailserver_rw').create(
            username='todelete@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        account_id = account.id
        result = delete_account(account_id)
        
        self.assertTrue(result)
        
        # 验证账户已被物理删除
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.using('mailserver_rw').get(id=account_id)
    
    def test_delete_account_not_found(self):
        """测试删除不存在的账户"""
        result = delete_account(99999)
        self.assertFalse(result)
    
    def test_list_accounts_ordering(self):
        """测试列表账户的排序（应该按创建时间倒序）"""
        accounts = []
        for i in range(5):
            account = MailAccount.objects.using('mailserver_rw').create(
                username=f'user{i}@example.com',
                password='pass',
                domain='example.com',
                is_active=True,
                ct=int(time.time() * 1000) + i * 1000,  # 确保时间不同
                ut=int(time.time() * 1000) + i * 1000
            )
            accounts.append(account)
        
        result = list_accounts()
        
        # 应该按 ct 倒序排列（最新的在前）
        result_ids = [acc.id for acc in result['accounts']]
        expected_ids = [acc.id for acc in reversed(accounts)]
        self.assertEqual(result_ids, expected_ids)

