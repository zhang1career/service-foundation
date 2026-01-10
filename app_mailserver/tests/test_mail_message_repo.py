"""
单元测试：MailMessage Repository

测试覆盖：
- create_mail_message
- get_mail_message_by_id
- get_messages_by_mailbox
- count_messages_by_mailbox
- count_unread_messages_by_mailbox
- update_message_read_status
- delete_mail_message
"""
import time
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.repos.mail_message_repo import (
    create_mail_message,
    get_mail_message_by_id,
    get_messages_by_mailbox,
    count_messages_by_mailbox,
    count_unread_messages_by_mailbox,
    update_message_read_status,
    delete_mail_message,
)


class TestMailMessageRepo(TransactionTestCase):
    """测试 MailMessage repository 函数"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前清理数据"""
        MailAccount.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailMessage.objects.using('mailserver_rw').all().delete()
        
        # 创建测试账户和邮箱
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        self.test_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
    
    def tearDown(self):
        """每个测试后清理数据"""
        MailMessage.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()
    
    def test_create_mail_message_success(self):
        """测试创建邮件消息成功"""
        message = create_mail_message(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<test@example.com>',
            subject='Test Subject',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            text_body='Test body',
            mt=int(time.time() * 1000),
            size=100
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.from_address, 'sender@example.com')
        self.assertEqual(message.text_body, 'Test body')
        self.assertGreater(message.ct, 0)
        
        # 验证数据库中已创建
        db_message = MailMessage.objects.using('mailserver_rw').get(id=message.id)
        self.assertEqual(db_message.subject, 'Test Subject')
    
    def test_get_mail_message_by_id_success(self):
        """测试根据ID获取邮件消息成功"""
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<test@example.com>',
            subject='Test Subject',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = get_mail_message_by_id(message.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, message.id)
        self.assertEqual(result.subject, 'Test Subject')
    
    def test_get_mail_message_by_id_not_found(self):
        """测试获取不存在的邮件消息"""
        result = get_mail_message_by_id(99999)
        self.assertIsNone(result)
    
    def test_get_messages_by_mailbox_success(self):
        """测试获取邮箱中的所有邮件"""
        # 创建多个邮件
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000) + 1000,
            size=100,
            ct=int(time.time() * 1000) + 1000,
            ut=int(time.time() * 1000) + 1000
        )
        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000) + 2000,
            size=200,
            ct=int(time.time() * 1000) + 2000,
            ut=int(time.time() * 1000) + 2000
        )
        
        result = get_messages_by_mailbox(self.test_mailbox.id)
        
        self.assertEqual(len(result), 2)
        result_ids = {msg.id for msg in result}
        self.assertIn(msg1.id, result_ids)
        self.assertIn(msg2.id, result_ids)
    
    
    def test_get_messages_by_mailbox_ordering(self):
        """测试邮件排序"""
        # 创建多个邮件，不同的时间戳
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=1000,
            size=100,
            ct=1000,
            ut=1000
        )
        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=2000,
            size=100,
            ct=2000,
            ut=2000
        )
        
        result = get_messages_by_mailbox(self.test_mailbox.id, order_by='mt')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, msg1.id)  # 按 mt 升序
        self.assertEqual(result[1].id, msg2.id)
    
    def test_count_messages_by_mailbox(self):
        """测试统计邮箱中的邮件数量"""
        # 创建多个邮件
        for i in range(5):
            MailMessage.objects.using('mailserver_rw').create(
                account_id=self.test_account.id,
                mailbox_id=self.test_mailbox.id,
                message_id=f'<msg{i}@example.com>',
                subject=f'Message {i}',
                from_address='sender@example.com',
                to_addresses='recipient@example.com',
                mt=int(time.time() * 1000) + i,
                size=100,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )
        
        count = count_messages_by_mailbox(self.test_mailbox.id)
        self.assertEqual(count, 5)
    
    def test_count_unread_messages_by_mailbox(self):
        """测试统计未读邮件数量"""
        # 创建已读和未读邮件
        for i in range(3):
            MailMessage.objects.using('mailserver_rw').create(
                account_id=self.test_account.id,
                mailbox_id=self.test_mailbox.id,
                message_id=f'<read{i}@example.com>',
                subject=f'Read {i}',
                from_address='sender@example.com',
                to_addresses='recipient@example.com',
                is_read=True,
                mt=int(time.time() * 1000) + i,
                size=100,
                ct=int(time.time() * 1000) + i,
                ut=int(time.time() * 1000) + i
            )
        
        for i in range(2):
            MailMessage.objects.using('mailserver_rw').create(
                account_id=self.test_account.id,
                mailbox_id=self.test_mailbox.id,
                message_id=f'<unread{i}@example.com>',
                subject=f'Unread {i}',
                from_address='sender@example.com',
                to_addresses='recipient@example.com',
                is_read=False,
                mt=int(time.time() * 1000) + i + 10,
                size=100,
                ct=int(time.time() * 1000) + i + 10,
                ut=int(time.time() * 1000) + i + 10
            )
        
        unread_count = count_unread_messages_by_mailbox(self.test_mailbox.id)
        self.assertEqual(unread_count, 2)
    
    def test_update_message_read_status(self):
        """测试更新邮件已读状态"""
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<test@example.com>',
            subject='Test',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        # 标记为已读
        rows_updated = update_message_read_status(self.test_mailbox.id, message.id, is_read=True)
        self.assertEqual(rows_updated, 1)
        
        # 验证已更新
        updated_message = MailMessage.objects.using('mailserver_rw').get(id=message.id)
        self.assertTrue(updated_message.is_read)
        
        # 标记为未读
        rows_updated = update_message_read_status(self.test_mailbox.id, message.id, is_read=False)
        self.assertEqual(rows_updated, 1)
        
        updated_message = MailMessage.objects.using('mailserver_rw').get(id=message.id)
        self.assertFalse(updated_message.is_read)
    
    def test_delete_mail_message(self):
        """测试删除邮件消息"""
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<test@example.com>',
            subject='Test',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        result = delete_mail_message(message.id)
        
        self.assertTrue(result)
        
        # 验证邮件已被删除（物理删除）
        with self.assertRaises(MailMessage.DoesNotExist):
            MailMessage.objects.using('mailserver_rw').get(id=message.id)
    
    def test_unique_constraint_account_message_id(self):
        """测试账户和Message-ID的唯一性约束"""
        # 创建第一个邮件
        message1 = create_mail_message(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<unique@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100
        )
        
        # 尝试创建相同Message-ID的邮件（应该失败）
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            create_mail_message(
                account_id=self.test_account.id,
                mailbox_id=self.test_mailbox.id,
                message_id='<unique@example.com>',  # 相同的 Message-ID
                subject='Message 2',
                from_address='sender@example.com',
                to_addresses='recipient@example.com',
                mt=int(time.time() * 1000),
                size=100
            )
        
        # 但不同账户可以有相同的 Message-ID
        other_account = MailAccount.objects.using('mailserver_rw').create(
            username='other@example.com',
            password='pass',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        other_mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=other_account.id,
            name='INBOX',
            path='INBOX',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        
        message2 = create_mail_message(
            account_id=other_account.id,
            mailbox_id=other_mailbox.id,
            message_id='<unique@example.com>',  # 相同的 Message-ID，但不同账户
            subject='Message 3',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100
        )
        
        self.assertIsNotNone(message2)
        self.assertNotEqual(message1.id, message2.id)

