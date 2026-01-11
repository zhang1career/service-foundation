"""
单元测试：Mailbox REST API 视图

测试覆盖：
- 创建邮箱 (POST)
- 获取邮箱列表 (GET with pagination)
- 获取邮箱详情 (GET by ID)
- 更新邮箱 (PUT/PATCH)
- 删除邮箱 (DELETE)
- 错误处理和验证
"""
import json
import time
from django.db import transaction, connections
from django.db.transaction import TransactionManagementError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.views.mailbox_view import (
    MailboxListView,
    MailboxDetailView,
)
from common.consts.response_const import RET_OK, RET_RESOURCE_NOT_FOUND


class TestMailboxListView(TestCase):
    """测试 MailboxListView (列表和创建)"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        self.factory = APIRequestFactory()
        self.view = MailboxListView.as_view()

        # 清理测试数据
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()

        # 创建测试账户
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 创建一些测试 mailbox
        self.test_mailboxes = []
        mailbox_names = ['INBOX', 'Sent', 'Drafts', 'Trash', 'Archive']
        for i, name in enumerate(mailbox_names):
            mailbox = Mailbox.objects.using('mailserver_rw').create(
                account_id=self.test_account.id,
                name=name,
                path=name,
                message_count=i * 2,
                unread_count=i,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )
            self.test_mailboxes.append(mailbox)

    def tearDown(self):
        """每个测试后清理"""
        try:
            Mailbox.objects.using('mailserver_rw').all().delete()
            MailAccount.objects.using('mailserver_rw').all().delete()
        except TransactionManagementError:
            connection = connections['mailserver_rw']
            if connection.in_atomic_block:
                transaction.set_rollback(True, using='mailserver_rw')

    def test_list_mailboxes_success(self):
        """测试成功获取邮箱列表"""
        view = MailboxListView.as_view()
        request = self.factory.get(f'/api/mail/accounts/{self.test_account.id}/mailboxes')
        response = view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        self.assertIn('data', response_data)

        page_data = response_data['data']
        self.assertIn('data', page_data)
        self.assertIn('total_num', page_data)
        self.assertIn('next_offset', page_data)

        # 验证返回的数据
        mailboxes = page_data['data']
        self.assertEqual(len(mailboxes), 5)
        self.assertEqual(page_data['total_num'], 5)
        self.assertIsNone(page_data['next_offset'])  # 所有数据都在第一页

        # 验证返回的 mailbox 字段
        if mailboxes:
            mailbox = mailboxes[0]
            self.assertIn('id', mailbox)
            self.assertIn('account_id', mailbox)
            self.assertIn('name', mailbox)
            self.assertIn('path', mailbox)
            self.assertIn('message_count', mailbox)
            self.assertIn('unread_count', mailbox)
            self.assertIn('ct', mailbox)
            self.assertIn('ut', mailbox)

    def test_list_mailboxes_with_pagination(self):
        """测试分页功能"""
        view = MailboxListView.as_view()
        request = self.factory.get(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            {'offset': 0, 'limit': 2}
        )
        response = view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']

        # 应该只返回 2 条记录
        self.assertEqual(len(page_data['data']), 2)
        self.assertEqual(page_data['total_num'], 5)
        self.assertEqual(page_data['next_offset'], 2)

    def test_list_mailboxes_pagination_last_page(self):
        """测试分页最后一页"""
        view = MailboxListView.as_view()
        request = self.factory.get(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            {'offset': 4, 'limit': 2}
        )
        response = view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']

        # 最后一页应该只返回 1 条记录
        self.assertEqual(len(page_data['data']), 1)
        self.assertEqual(page_data['total_num'], 5)
        self.assertIsNone(page_data['next_offset'])  # 没有下一页

    def test_list_mailboxes_with_limit_exceeding_max(self):
        """测试 limit 超过最大值时应该被限制为 1000"""
        view = MailboxListView.as_view()
        request = self.factory.get(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            {'offset': 0, 'limit': 5000}
        )
        response = view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']

        # 应该返回所有数据（因为总数小于 1000）
        self.assertEqual(len(page_data['data']), 5)
        self.assertEqual(page_data['total_num'], 5)

    def test_list_mailboxes_empty_account(self):
        """测试空账户的邮箱列表"""
        # 创建新账户，没有任何 mailbox
        new_account = MailAccount.objects.using('mailserver_rw').create(
            username='empty@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        view = MailboxListView.as_view()
        request = self.factory.get(f'/api/mail/accounts/{new_account.id}/mailboxes')
        response = view(request, account_id=new_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']

        # 应该返回空列表
        self.assertEqual(len(page_data['data']), 0)
        self.assertEqual(page_data['total_num'], 0)
        self.assertIsNone(page_data['next_offset'])

    def test_list_mailboxes_account_not_found(self):
        """测试账户不存在时的错误处理"""
        view = MailboxListView.as_view()
        non_existent_id = 99999
        request = self.factory.get(f'/api/mail/accounts/{non_existent_id}/mailboxes')
        response = view(request, account_id=non_existent_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())

    def test_list_mailboxes_multi_account_isolation(self):
        """测试多个账户之间的邮箱隔离"""
        # 创建另一个账户和邮箱
        other_account = MailAccount.objects.using('mailserver_rw').create(
            username='other@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        Mailbox.objects.using('mailserver_rw').create(
            account_id=other_account.id,
            name='OtherInbox',
            path='OtherInbox',
            message_count=10,
            unread_count=5,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 查询第一个账户的邮箱
        request = self.factory.get(f'/api/mail/accounts/{self.test_account.id}/mailboxes')
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        page_data = response_data['data']

        # 应该只返回第一个账户的邮箱，不应该包含第二个账户的邮箱
        self.assertEqual(page_data['total_num'], 5)
        mailbox_paths = [mb['path'] for mb in page_data['data']]
        self.assertNotIn('OtherInbox', mailbox_paths)
        self.assertIn('INBOX', mailbox_paths)

    def test_create_mailbox_success(self):
        """测试成功创建邮箱"""
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'name': 'TestFolder',
                'path': 'TestFolder',
                'message_count': 5,
                'unread_count': 2
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)

        mailbox_data = response_data['data']
        self.assertEqual(mailbox_data['name'], 'TestFolder')
        self.assertEqual(mailbox_data['path'], 'TestFolder')
        self.assertEqual(mailbox_data['account_id'], self.test_account.id)
        self.assertEqual(mailbox_data['message_count'], 5)
        self.assertEqual(mailbox_data['unread_count'], 2)
        self.assertIn('id', mailbox_data)

        # 验证数据库中已创建
        mailbox = Mailbox.objects.using('mailserver_rw').get(
            account_id=self.test_account.id,
            path='TestFolder'
        )
        self.assertEqual(mailbox.name, 'TestFolder')

    def test_create_mailbox_with_nested_path(self):
        """测试创建嵌套路径的邮箱"""
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'name': 'Sent',
                'path': 'INBOX.Sent',
                'message_count': 10,
                'unread_count': 1
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        mailbox_data = response_data['data']

        self.assertEqual(mailbox_data['name'], 'Sent')
        self.assertEqual(mailbox_data['path'], 'INBOX.Sent')

    def test_create_mailbox_duplicate_path(self):
        """测试创建重复路径的邮箱（应该返回错误）"""
        # 尝试创建已存在的路径
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'name': 'INBOX',
                'path': 'INBOX',
                'message_count': 0,
                'unread_count': 0
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('already exists', response_data['message'].lower())

    def test_create_mailbox_missing_name(self):
        """测试缺少名称时创建邮箱（应该返回错误）"""
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'path': 'TestPath',
                'message_count': 0
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('required', response_data['message'].lower())

    def test_create_mailbox_missing_path(self):
        """测试缺少路径时创建邮箱（应该返回错误）"""
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'name': 'TestName',
                'message_count': 0
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('required', response_data['message'].lower())

    def test_create_mailbox_account_not_found(self):
        """测试为不存在的账户创建邮箱（应该返回错误）"""
        non_existent_account_id = 99999
        request = self.factory.post(
            f'/api/mail/accounts/{non_existent_account_id}/mailboxes',
            data={
                'name': 'TestFolder',
                'path': 'TestFolder'
            },
            format='json'
        )
        response = self.view(request, account_id=non_existent_account_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('not found', response_data['message'].lower())

    def test_create_mailbox_with_default_counts(self):
        """测试创建邮箱时使用默认计数"""
        request = self.factory.post(
            f'/api/mail/accounts/{self.test_account.id}/mailboxes',
            data={
                'name': 'NewFolder',
                'path': 'NewFolder'
            },
            format='json'
        )
        response = self.view(request, account_id=self.test_account.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        mailbox_data = response_data['data']

        # 应该使用默认值 0
        self.assertEqual(mailbox_data['message_count'], 0)
        self.assertEqual(mailbox_data['unread_count'], 0)


class TestMailboxDetailView(TestCase):
    """测试 MailboxDetailView (详情、更新、删除)"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        self.factory = APIRequestFactory()
        self.view = MailboxDetailView.as_view()

        # 清理测试数据
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()

        # 创建测试账户
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 创建测试 mailbox
        self.test_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=10,
            unread_count=3,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        self.mailbox_id = self.test_mailbox.id

    def tearDown(self):
        """每个测试后清理"""
        try:
            Mailbox.objects.using('mailserver_rw').all().delete()
            MailAccount.objects.using('mailserver_rw').all().delete()
        except TransactionManagementError:
            connection = connections['mailserver_rw']
            if connection.in_atomic_block:
                transaction.set_rollback(True, using='mailserver_rw')

    def test_get_mailbox_success(self):
        """测试成功获取邮箱详情"""
        request = self.factory.get(f'/api/mail/mailboxes/{self.mailbox_id}')
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)

        mailbox_data = response_data['data']
        self.assertEqual(mailbox_data['id'], self.mailbox_id)
        self.assertEqual(mailbox_data['account_id'], self.test_account.id)
        self.assertEqual(mailbox_data['name'], 'INBOX')
        self.assertEqual(mailbox_data['path'], 'INBOX')
        self.assertEqual(mailbox_data['message_count'], 10)
        self.assertEqual(mailbox_data['unread_count'], 3)
        self.assertIn('ct', mailbox_data)
        self.assertIn('ut', mailbox_data)

    def test_get_mailbox_not_found(self):
        """测试获取不存在的邮箱"""
        non_existent_id = 99999
        request = self.factory.get(f'/api/mail/mailboxes/{non_existent_id}')
        response = self.view(request, mailbox_id=non_existent_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())

    def test_get_mailbox_with_nested_path(self):
        """测试获取嵌套路径的邮箱"""
        # 创建嵌套路径的 mailbox（如 INBOX.Sent）
        nested_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='Sent',
            path='INBOX.Sent',
            message_count=5,
            unread_count=1,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        request = self.factory.get(f'/api/mail/mailboxes/{nested_mailbox.id}')
        response = self.view(request, mailbox_id=nested_mailbox.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        mailbox_data = response_data['data']

        self.assertEqual(mailbox_data['name'], 'Sent')
        self.assertEqual(mailbox_data['path'], 'INBOX.Sent')

    def test_get_mailbox_all_fields(self):
        """测试返回所有字段的完整性"""
        request = self.factory.get(f'/api/mail/mailboxes/{self.mailbox_id}')
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        mailbox_data = response_data['data']

        # 验证所有字段都存在
        required_fields = ['id', 'account_id', 'name', 'path', 'message_count',
                           'unread_count', 'ct', 'ut']
        for field in required_fields:
            self.assertIn(field, mailbox_data)

    def test_update_mailbox_success(self):
        """测试成功更新邮箱"""
        request = self.factory.put(
            f'/api/mail/mailboxes/{self.mailbox_id}',
            data={
                'name': 'UpdatedName',
                'path': 'UpdatedPath',
                'message_count': 20,
                'unread_count': 5
            },
            format='json'
        )
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)

        mailbox_data = response_data['data']
        self.assertEqual(mailbox_data['name'], 'UpdatedName')
        self.assertEqual(mailbox_data['path'], 'UpdatedPath')
        self.assertEqual(mailbox_data['message_count'], 20)
        self.assertEqual(mailbox_data['unread_count'], 5)

        # 验证数据库已更新
        updated_mailbox = Mailbox.objects.using('mailserver_rw').get(id=self.mailbox_id)
        self.assertEqual(updated_mailbox.name, 'UpdatedName')
        self.assertEqual(updated_mailbox.path, 'UpdatedPath')
        self.assertEqual(updated_mailbox.message_count, 20)
        self.assertEqual(updated_mailbox.unread_count, 5)

    def test_partial_update_mailbox(self):
        """测试部分更新邮箱（只更新部分字段）"""
        request = self.factory.patch(
            f'/api/mail/mailboxes/{self.mailbox_id}',
            data={
                'message_count': 15,
                'unread_count': 4
            },
            format='json'
        )
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        mailbox_data = response_data['data']

        # message_count 和 unread_count 应该更新
        self.assertEqual(mailbox_data['message_count'], 15)
        self.assertEqual(mailbox_data['unread_count'], 4)
        # 其他字段应该保持不变
        self.assertEqual(mailbox_data['name'], 'INBOX')
        self.assertEqual(mailbox_data['path'], 'INBOX')

        # 验证数据库
        updated_mailbox = Mailbox.objects.using('mailserver_rw').get(id=self.mailbox_id)
        self.assertEqual(updated_mailbox.message_count, 15)
        self.assertEqual(updated_mailbox.unread_count, 4)
        self.assertEqual(updated_mailbox.name, 'INBOX')
        self.assertEqual(updated_mailbox.path, 'INBOX')

    def test_update_mailbox_not_found(self):
        """测试更新不存在的邮箱（应该返回错误）"""
        non_existent_id = 99999
        request = self.factory.put(
            f'/api/mail/mailboxes/{non_existent_id}',
            data={'name': 'NewName'},
            format='json'
        )
        response = self.view(request, mailbox_id=non_existent_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())

    def test_update_mailbox_with_duplicate_path(self):
        """测试更新为已存在的路径（应该返回错误）"""
        # 创建另一个邮箱
        other_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='OtherFolder',
            path='OtherFolder',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 尝试将当前邮箱更新为已存在的路径
        request = self.factory.put(
            f'/api/mail/mailboxes/{self.mailbox_id}',
            data={
                'path': 'OtherFolder'
            },
            format='json'
        )
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('already exists', response_data['message'].lower())

    def test_update_mailbox_empty_name(self):
        """测试更新为空名称（应该返回错误）"""
        request = self.factory.put(
            f'/api/mail/mailboxes/{self.mailbox_id}',
            data={
                'name': ''
            },
            format='json'
        )
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('cannot be empty', response_data['message'].lower())

    def test_update_mailbox_negative_counts(self):
        """测试更新为负数计数（应该返回错误）"""
        request = self.factory.put(
            f'/api/mail/mailboxes/{self.mailbox_id}',
            data={
                'message_count': -1
            },
            format='json'
        )
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertNotEqual(response_data['errorCode'], RET_OK)
        self.assertIn('cannot be negative', response_data['message'].lower())

    def test_delete_mailbox_success(self):
        """测试成功删除邮箱（硬删除）"""
        request = self.factory.delete(f'/api/mail/mailboxes/{self.mailbox_id}')
        response = self.view(request, mailbox_id=self.mailbox_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_OK)
        self.assertIn('deleted', response_data['data']['message'].lower())

        # 验证邮箱已被物理删除
        with self.assertRaises(Mailbox.DoesNotExist):
            Mailbox.objects.using('mailserver_rw').get(id=self.mailbox_id)

    def test_delete_mailbox_not_found(self):
        """测试删除不存在的邮箱（应该返回错误）"""
        non_existent_id = 99999
        request = self.factory.delete(f'/api/mail/mailboxes/{non_existent_id}', format='json')
        response = self.view(request, mailbox_id=non_existent_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        response_data = json.loads(response.content)
        self.assertEqual(response_data['errorCode'], RET_RESOURCE_NOT_FOUND)
        self.assertIn('not found', response_data['message'].lower())
