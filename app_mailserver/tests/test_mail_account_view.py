"""
单元测试：MailAccount REST API 视图

测试覆盖：
- 创建邮件账户 (POST)
- 获取邮件账户列表 (GET with pagination/filtering)
- 获取邮件账户详情 (GET by ID)
- 更新邮件账户 (PUT/PATCH)
- 删除邮件账户 (DELETE)
- 错误处理和验证
"""
import json
import time
from django.db import transaction, connections
from django.db.transaction import TransactionManagementError
from django.test import TestCase
from rest_framework.test import APIRequestFactory, APIClient
from rest_framework import status

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.views.mail_account_view import (
    MailAccountListView,
    MailAccountDetailView,
)
from common.consts.response_const import RET_OK, RET_RESOURCE_NOT_FOUND


class TestMailAccountListView(TestCase):
    """测试 MailAccountListView (列表和创建)"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.view = MailAccountListView.as_view()
        
        # 清理测试数据
        MailAccount.objects.using('mailserver_rw').all().delete()
        
        # 创建一些测试数据
        self.test_accounts = []
        for i in range(5):
            account = MailAccount.objects.using('mailserver_rw').create(
                username=f'user{i}@example.com',
                password=f'password{i}',
                domain='example.com',
                is_active=True,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )
            self.test_accounts.append(account)
    
    def tearDown(self):
        """每个测试后清理"""
        # 如果事务已损坏（例如由于完整性约束错误），设置回滚标志
        # Django 的 TestCase 会在每个测试后自动回滚所有事务，所以不需要手动删除
        try:
            MailAccount.objects.using('mailserver_rw').all().delete()
        except TransactionManagementError:
            # 事务已损坏，设置回滚标志让 Django 测试框架自动回滚
            # 不能直接调用 rollback()，因为测试框架在原子块中运行
            connection = connections['mailserver_rw']
            if connection.in_atomic_block:
                # 在原子块中，设置回滚标志让框架自动处理
                transaction.set_rollback(True, using='mailserver_rw')
            # 设置回滚后，数据会被框架自动回滚，不需要手动删除

    def test_list_accounts_success(self):
        """测试成功获取账户列表"""
        request = self.factory.get('/api/mail/accounts')
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        self.assertIn('data', response_data)
        
        page_data = response_data['data']
        self.assertIn('data', page_data)
        self.assertIn('total_num', page_data)
        self.assertIn('next_offset', page_data)
        
        # 验证返回的数据
        accounts = page_data['data']
        self.assertGreater(len(accounts), 0)
        self.assertEqual(page_data['total_num'], 5)
        
        # 验证返回的账户字段
        if accounts:
            account = accounts[0]
            self.assertIn('id', account)
            self.assertIn('username', account)
            self.assertIn('domain', account)
            self.assertIn('is_active', account)
            self.assertIn('ct', account)
            self.assertIn('ut', account)
    
    def test_list_accounts_with_pagination(self):
        """测试分页功能"""
        request = self.factory.get('/api/mail/accounts', {'offset': 0, 'limit': 2})
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']
        
        # 应该只返回 2 条记录
        self.assertEqual(len(page_data['data']), 2)
        self.assertEqual(page_data['total_num'], 5)
        self.assertEqual(page_data['next_offset'], 2)
    
    def test_list_accounts_with_domain_filter(self):
        """测试按域名筛选"""
        # 创建一个不同域名的账户
        MailAccount.objects.using('mailserver_rw').create(
            username='other@otherdomain.com',
            password='pass',
            domain='otherdomain.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        request = self.factory.get('/api/mail/accounts', {'domain': 'example.com'})
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']
        
        # 应该只返回 example.com 域名的账户
        self.assertEqual(page_data['total_num'], 5)
        for account in page_data['data']:
            self.assertEqual(account['domain'], 'example.com')
    
    def test_list_accounts_with_is_active_filter(self):
        """测试按激活状态筛选"""
        # 创建一个非激活账户
        MailAccount.objects.using('mailserver_rw').create(
            username='inactive@example.com',
            password='pass',
            domain='example.com',
            is_active=False,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        request = self.factory.get('/api/mail/accounts', {'is_active': 'true'})
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']
        
        # 应该只返回激活的账户
        for account in page_data['data']:
            self.assertTrue(account['is_active'])
    
    def test_list_accounts_with_username(self):
        """测试按 username 搜索功能（多个账户包含相同的子字符串）"""
        # 清理测试数据
        MailAccount.objects.using('mailserver_rw').all().delete()
        
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
        # 创建一个不包含 "zzz" 的账户
        MailAccount.objects.using('mailserver_rw').create(
            username='normal_user@example.com',
            password='pass4',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 4,
            ut=int(time.time() * 1000) + 4
        )
        # 创建另一个不包含 "zzz" 的账户
        MailAccount.objects.using('mailserver_rw').create(
            username='other_user@example.com',
            password='pass5',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000) + 5,
            ut=int(time.time() * 1000) + 5
        )
        
        # 使用 username 参数搜索包含 "zzz" 的账户
        request = self.factory.get('/api/mail/accounts', {'username': 'zzz'})
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        page_data = response_data['data']
        
        # 应该返回包含 'zzz' 的账户（应该返回 3 个）
        self.assertEqual(page_data['total_num'], 3)
        self.assertEqual(len(page_data['data']), 3)
        
        # 验证所有返回的账户都包含 'zzz'
        returned_usernames = []
        for account in page_data['data']:
            self.assertIn('zzz', account['username'].lower())
            returned_usernames.append(account['username'])
        
        # 验证返回了所有包含 "zzz" 的账户
        expected_usernames = {'zzz_user1@example.com', 'zzz_user2@example.com', 'admin_zzz@example.com'}
        actual_usernames = set(returned_usernames)
        self.assertEqual(actual_usernames, expected_usernames)
        
        # 验证不包含 "zzz" 的账户没有被返回
        self.assertNotIn('normal_user@example.com', returned_usernames)
        self.assertNotIn('other_user@example.com', returned_usernames)
    
    def test_create_account_success(self):
        """测试成功创建账户"""
        request = self.factory.post(
            '/api/mail/accounts',
            data={
                'username': 'newuser@example.com',
                'password': 'newpassword',
                'domain': 'example.com',
                'is_active': True
            },
            format='json'
        )
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        
        account_data = response_data['data']
        self.assertEqual(account_data['username'], 'newuser@example.com')
        self.assertEqual(account_data['domain'], 'example.com')
        self.assertTrue(account_data['is_active'])
        self.assertIn('id', account_data)
        
        # 验证数据库中已创建
        account = MailAccount.objects.using('mailserver_rw').get(username='newuser@example.com')
        self.assertEqual(account.password, 'newpassword')
    
    def test_create_account_with_auto_domain(self):
        """测试创建账户时自动提取域名"""
        request = self.factory.post(
            '/api/mail/accounts',
            data={
                'username': 'auto@testdomain.com',
                'password': 'pass',
                'is_active': True
            },
            format='json'
        )
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        account_data = response_data['data']
        
        # 应该自动提取域名为 testdomain.com
        self.assertEqual(account_data['domain'], 'testdomain.com')
    
    def test_create_account_duplicate_username(self):
        """测试创建重复用户名的账户（应该返回错误）"""
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
        request = self.factory.post(
            '/api/mail/accounts',
            data={
                'username': 'duplicate@example.com',
                'password': 'pass2',
                'domain': 'example.com',
                'is_active': True
            },
            format='json'
        )
        response = self.view(request)
        
        # 应该返回 HTTP 200 但 errorCode 为非0
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        # 应该包含错误信息
        self.assertNotEqual(response_data['errorCode'], RET_OK)

    def test_create_account_missing_username(self):
        """测试缺少用户名时创建账户（应该返回错误）"""
        request = self.factory.post(
            '/api/mail/accounts',
            data={
                'password': 'pass',
                'domain': 'example.com'
            },
            format='json'
        )
        response = self.view(request)
        
        # 应该返回 HTTP 200 但 errorCode 为非0
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('username', response_data['message'].lower())


class TestMailAccountDetailView(TestCase):
    """测试 MailAccountDetailView (详情、更新、删除)"""
    
    databases = {'default', 'mailserver_rw'}
    
    def setUp(self):
        """每个测试前设置"""
        self.factory = APIRequestFactory()
        self.view = MailAccountDetailView.as_view()
        
        # 清理测试数据 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        # Django 的 TestCase 会在每个测试开始时自动开始新事务，所以这里应该不会有损坏的事务
        MailAccount.objects.using('mailserver_rw').all().delete()
        
        # 创建测试账户 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='testpassword',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        self.account_id = self.test_account.id
    
    def tearDown(self):
        """每个测试后清理"""
        # 如果事务已损坏（例如由于完整性约束错误），设置回滚标志
        # Django 的 TestCase 会在每个测试后自动回滚所有事务，所以不需要手动删除
        try:
            MailAccount.objects.using('mailserver_rw').all().delete()
        except TransactionManagementError:
            # 事务已损坏，设置回滚标志让 Django 测试框架自动回滚
            # 不能直接调用 rollback()，因为测试框架在原子块中运行
            connection = connections['mailserver_rw']
            if connection.in_atomic_block:
                # 在原子块中，设置回滚标志让框架自动处理
                transaction.set_rollback(True, using='mailserver_rw')
            # 设置回滚后，数据会被框架自动回滚，不需要手动删除
    
    def test_get_account_success(self):
        """测试成功获取账户详情"""
        request = self.factory.get(f'/api/mail/accounts/{self.account_id}')
        response = self.view(request, account_id=self.account_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        
        account_data = response_data['data']
        self.assertEqual(account_data['id'], self.account_id)
        self.assertEqual(account_data['username'], 'test@example.com')
        self.assertEqual(account_data['domain'], 'example.com')
        self.assertTrue(account_data['is_active'])
    
    def test_get_account_not_found(self):
        """测试获取不存在的账户"""
        non_existent_id = 99999
        request = self.factory.get(f'/api/mail/accounts/{non_existent_id}')
        response = self.view(request, account_id=non_existent_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())
    
    def test_update_account_success(self):
        """测试成功更新账户"""
        request = self.factory.put(
            f'/api/mail/accounts/{self.account_id}',
            data={
                'username': 'updated@example.com',
                'password': 'newpassword',
                'domain': 'newdomain.com',
                'is_active': False
            },
            format='json'
        )
        response = self.view(request, account_id=self.account_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        
        account_data = response_data['data']
        self.assertEqual(account_data['username'], 'updated@example.com')
        self.assertEqual(account_data['domain'], 'newdomain.com')
        self.assertFalse(account_data['is_active'])
        
        # 验证数据库已更新 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        updated_account = MailAccount.objects.using('mailserver_rw').get(id=self.account_id)
        self.assertEqual(updated_account.username, 'updated@example.com')
        self.assertEqual(updated_account.password, 'newpassword')
        self.assertEqual(updated_account.domain, 'newdomain.com')
        self.assertFalse(updated_account.is_active)
    
    def test_partial_update_account(self):
        """测试部分更新账户（只更新部分字段）"""
        request = self.factory.patch(
            f'/api/mail/accounts/{self.account_id}',
            data={
                'password': 'updatedpassword',
                'is_active': False
            },
            format='json'
        )
        response = self.view(request, account_id=self.account_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        account_data = response_data['data']
        
        # 密码和 is_active 应该更新
        self.assertFalse(account_data['is_active'])
        # 其他字段应该保持不变
        self.assertEqual(account_data['username'], 'test@example.com')
        self.assertEqual(account_data['domain'], 'example.com')
        
        # 验证数据库 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        updated_account = MailAccount.objects.using('mailserver_rw').get(id=self.account_id)
        self.assertEqual(updated_account.password, 'updatedpassword')
        self.assertFalse(updated_account.is_active)
        self.assertEqual(updated_account.username, 'test@example.com')
    
    def test_update_account_not_found(self):
        """测试更新不存在的账户（应该返回 HTTP 200 但 errorCode 为 404）"""
        non_existent_id = 99999
        request = self.factory.put(
            f'/api/mail/accounts/{non_existent_id}',
            data={'username': 'new@example.com'},
            format='json'
        )
        response = self.view(request, account_id=non_existent_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())
    
    def test_delete_account_success(self):
        """测试成功删除账户（硬删除）"""
        request = self.factory.delete(f'/api/mail/accounts/{self.account_id}')
        response = self.view(request, account_id=self.account_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        self.assertIn('deleted', response_data['data']['message'].lower())
        
        # 验证账户已被物理删除 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.using('mailserver_rw').get(id=self.account_id)
    
    def test_delete_account_not_found(self):
        """测试删除不存在的账户（应该返回 HTTP 200 但 errorCode 为 404）"""
        non_existent_id = 99999
        # Use format='json' to set Accept header for JSON response rendering
        request = self.factory.delete(f'/api/mail/accounts/{non_existent_id}', format='json')
        response = self.view(request, account_id=non_existent_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For DRF Response objects, render before accessing content
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())
    
    def test_update_with_duplicate_username(self):
        """测试更新为已存在的用户名（应该返回错误）"""
        # 创建另一个账户 - 使用 mailserver_rw 数据库，与仓库代码保持一致
        other_account = MailAccount.objects.using('mailserver_rw').create(
            username='other@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        # 尝试将当前账户更新为已存在的用户名
        request = self.factory.put(
            f'/api/mail/accounts/{self.account_id}',
            data={
                'username': 'other@example.com',
                'password': 'pass2'
            },
            format='json'
        )
        response = self.view(request, account_id=self.account_id)
        
        # 应该返回 409 Conflict 或错误
        self.assertIn(response.status_code, [status.HTTP_409_CONFLICT, status.HTTP_200_OK])
        # For DRF Response objects, render before accessing content
        response.render()
        if response.status_code == status.HTTP_200_OK:
            response_data = json.loads(response.content)
            self.assertNotEqual(response_data['errorCode'], RET_OK)

