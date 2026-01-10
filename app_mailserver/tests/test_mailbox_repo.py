"""
单元测试：Mailbox Repository

测试覆盖：
- get_mailbox_by_account_and_path
- get_mailboxes_by_account
- get_or_create_mailbox
- get_mailbox_by_id
- update_mailbox
"""
import time
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.repos.mailbox_repo import (
    get_mailbox_by_account_and_path,
    get_mailboxes_by_account,
    get_or_create_mailbox,
    get_mailbox_by_id,
    update_mailbox,
)


class TestMailboxRepo(TransactionTestCase):
    """测试 Mailbox repository 函数"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前清理数据"""
        MailAccount.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()

        # 创建测试账户
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

    def tearDown(self):
        """每个测试后清理数据"""
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()

    def test_get_mailbox_by_account_and_path_success(self):
        """测试根据账户ID和路径获取邮箱成功"""
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        result = get_mailbox_by_account_and_path(self.test_account.id, 'INBOX')

        self.assertIsNotNone(result)
        self.assertEqual(result.id, mailbox.id)
        self.assertEqual(result.path, 'INBOX')
        self.assertEqual(result.account_id, self.test_account.id)

    def test_get_mailbox_by_account_and_path_not_found(self):
        """测试获取不存在的邮箱"""
        result = get_mailbox_by_account_and_path(self.test_account.id, 'NONEXISTENT')
        self.assertIsNone(result)

    def test_get_mailboxes_by_account_success(self):
        """测试获取账户的所有邮箱"""
        # 创建多个邮箱
        inbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        sent = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='Sent',
            path='Sent',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 为另一个账户创建邮箱（不应返回）
        other_account = MailAccount.objects.using('mailserver_rw').create(
            username='other@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        Mailbox.objects.using('mailserver_rw').create(
            account_id=other_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        result = get_mailboxes_by_account(self.test_account.id)

        self.assertEqual(len(result), 2)
        result_paths = {mb.path for mb in result}
        self.assertIn('INBOX', result_paths)
        self.assertIn('Sent', result_paths)

    def test_get_mailboxes_by_account_empty(self):
        """测试获取空账户的邮箱列表"""
        result = get_mailboxes_by_account(self.test_account.id)
        self.assertEqual(len(result), 0)

    def test_get_or_create_mailbox_create_new(self):
        """测试创建新邮箱"""
        mailbox, created = get_or_create_mailbox(
            account_id=self.test_account.id,
            path='INBOX',
            name='INBOX',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        self.assertTrue(created)
        self.assertIsNotNone(mailbox)
        self.assertEqual(mailbox.path, 'INBOX')
        self.assertEqual(mailbox.name, 'INBOX')
        self.assertEqual(mailbox.account_id, self.test_account.id)

        # 验证数据库中已创建
        db_mailbox = Mailbox.objects.using('mailserver_rw').get(id=mailbox.id)
        self.assertEqual(db_mailbox.path, 'INBOX')

    def test_get_or_create_mailbox_get_existing(self):
        """测试获取已存在的邮箱"""
        # 先创建邮箱
        existing_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=5,
            unread_count=2,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        mailbox, created = get_or_create_mailbox(
            account_id=self.test_account.id,
            path='INBOX',
            name='INBOX',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        self.assertFalse(created)
        self.assertEqual(mailbox.id, existing_mailbox.id)
        self.assertEqual(mailbox.message_count, 5)  # 应该保持原有值

    def test_get_or_create_mailbox_auto_name(self):
        """测试自动提取邮箱名称"""
        mailbox, created = get_or_create_mailbox(
            account_id=self.test_account.id,
            path='INBOX.Sent',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        self.assertTrue(created)
        self.assertEqual(mailbox.path, 'INBOX.Sent')
        self.assertEqual(mailbox.name, 'Sent')  # 应该自动提取最后一个部分

    def test_get_mailbox_by_id_success(self):
        """测试根据ID获取邮箱成功"""
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        result = get_mailbox_by_id(mailbox.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, mailbox.id)
        self.assertEqual(result.path, 'INBOX')

    def test_get_mailbox_by_id_not_found(self):
        """测试获取不存在的邮箱"""
        result = get_mailbox_by_id(99999)
        self.assertIsNone(result)

    def test_update_mailbox_success(self):
        """测试更新邮箱字段"""
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        rows_updated = update_mailbox(
            mailbox,
            message_count=10,
            unread_count=3,
            name='Inbox'
        )

        self.assertEqual(rows_updated, 1)

        # 验证数据库已更新
        updated_mailbox = Mailbox.objects.using('mailserver_rw').get(id=mailbox.id)
        self.assertEqual(updated_mailbox.message_count, 10)
        self.assertEqual(updated_mailbox.unread_count, 3)
        self.assertEqual(updated_mailbox.name, 'Inbox')
        # 路径不应该改变
        self.assertEqual(updated_mailbox.path, 'INBOX')

    def test_update_mailbox_partial(self):
        """测试部分更新邮箱（只更新部分字段）"""
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=5,
            unread_count=2,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        rows_updated = update_mailbox(mailbox, message_count=10)

        self.assertEqual(rows_updated, 1)

        # 验证只更新了指定字段
        updated_mailbox = Mailbox.objects.using('mailserver_rw').get(id=mailbox.id)
        self.assertEqual(updated_mailbox.message_count, 10)
        self.assertEqual(updated_mailbox.unread_count, 2)  # 应该保持不变
        self.assertEqual(updated_mailbox.name, 'INBOX')  # 应该保持不变

    def test_unique_constraint_account_path(self):
        """测试账户和路径的唯一性约束"""
        # 创建第一个邮箱
        mailbox1, created1 = get_or_create_mailbox(
            account_id=self.test_account.id,
            path='INBOX',
            name='INBOX',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        self.assertTrue(created1)

        # 尝试创建相同路径的邮箱（应该获取已存在的）
        mailbox2, created2 = get_or_create_mailbox(
            account_id=self.test_account.id,
            path='INBOX',
            name='INBOX',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        self.assertFalse(created2)
        self.assertEqual(mailbox1.id, mailbox2.id)

        # 但不同账户可以有相同路径
        other_account = MailAccount.objects.create(
            username='other@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        mailbox3, created3 = get_or_create_mailbox(
            account_id=other_account.id,
            path='INBOX',
            name='INBOX',
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        self.assertTrue(created3)
        self.assertNotEqual(mailbox1.id, mailbox3.id)
