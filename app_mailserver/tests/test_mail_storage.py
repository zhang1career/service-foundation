"""
单元测试：MailStorageService 邮件存储服务

测试覆盖：
- store_mail (存储邮件和附件)
- retrieve_mail (检索邮件)
- get_attachment_data (获取附件数据)
- delete_mail (删除邮件)
- _sanitize_filename (文件名清理)
- _generate_message_id (生成消息ID)
"""
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from unittest.mock import Mock, patch, MagicMock
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.services.mail_storage import MailStorageService, get_storage_service
from common.enums.content_type_enum import ContentTypeEnum


class TestMailStorageService(TransactionTestCase):
    """测试 MailStorageService"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        MailAccount.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailMessage.objects.using('mailserver_rw').all().delete()
        
        # 创建测试账户
        self.test_account = MailAccount.objects.using('mailserver_rw').create(
            username='test@example.com',
            password='password',
            domain='example.com',
            is_active=True,
            ct=int(time.time() * 1000),
            dt=int(time.time() * 1000)
        )
        
        # Mock OSS service
        self.mock_oss_service = Mock()
        self.mock_oss_service.upload_attachment.return_value = {
            'bucket': 'mail-attachments',
            'key': '1/1/test.pdf',
            'size': 1024
        }
        self.mock_oss_service.download_attachment.return_value = b'attachment data'
        self.mock_oss_service.delete_attachment.return_value = True
        
        # 创建存储服务实例，注入 mock OSS service
        self.storage_service = MailStorageService()
        self.storage_service.oss_service = self.mock_oss_service
    
    def tearDown(self):
        """每个测试后清理"""
        MailMessage.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()
    
    def test_store_simple_email(self):
        """测试存储简单邮件"""
        msg = MIMEText('This is a test email.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'test@example.com'
        msg['Subject'] = 'Test Subject'
        msg['Message-ID'] = '<test123@example.com>'
        
        email_data = msg.as_bytes()
        mail_message = self.storage_service.store_mail(
            account=self.test_account,
            mailbox_name='INBOX',
            email_data=email_data
        )
        
        self.assertIsNotNone(mail_message)
        self.assertEqual(mail_message.subject, 'Test Subject')
        self.assertEqual(mail_message.from_address, 'sender@example.com')
        self.assertIn('This is a test email.', mail_message.text_body)
        
        # 验证邮箱已创建或更新
        mailbox = Mailbox.objects.using('mailserver_rw').filter(account_id=self.test_account.id, path='INBOX').first()
        self.assertIsNotNone(mailbox)
        self.assertEqual(mailbox.message_count, 1)
        
        # 验证邮件已保存
        db_message = MailMessage.objects.using('mailserver_rw').get(id=mail_message.id)
        self.assertEqual(db_message.subject, 'Test Subject')
    
    def test_store_email_with_attachment(self):
        """测试存储带附件的邮件"""
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'test@example.com'
        msg['Subject'] = 'Email with Attachment'
        msg['Message-ID'] = '<attach123@example.com>'
        
        msg.attach(MIMEText('Email body.', 'plain'))
        
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(b'PDF content')
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
        msg.attach(attachment)
        
        email_data = msg.as_bytes()
        mail_message = self.storage_service.store_mail(
            account=self.test_account,
            mailbox_name='INBOX',
            email_data=email_data
        )
        
        self.assertIsNotNone(mail_message)
        
        # 验证 OSS service 被调用来上传附件
        self.mock_oss_service.upload_attachment.assert_called_once()
        
        # 验证附件记录已创建
        from app_mailserver.models.mail_attachment import MailAttachment
        attachments = MailAttachment.objects.using('mailserver_rw').filter(message_id=mail_message.id)
        self.assertEqual(attachments.count(), 1)
        self.assertEqual(attachments.first().filename, 'document.pdf')
    
    def test_store_email_creates_mailbox(self):
        """测试存储邮件时自动创建邮箱"""
        msg = MIMEText('Test email.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'test@example.com'
        msg['Subject'] = 'Test'
        msg['Message-ID'] = '<test123@example.com>'
        
        email_data = msg.as_bytes()
        mail_message = self.storage_service.store_mail(
            account=self.test_account,
            mailbox_name='Sent',
            email_data=email_data
        )
        
        # 验证 Sent 邮箱已创建
        mailbox = Mailbox.objects.using('mailserver_rw').filter(account_id=self.test_account.id, path='Sent').first()
        self.assertIsNotNone(mailbox)
        self.assertEqual(mailbox.name, 'Sent')
    
    def test_store_email_updates_mailbox_count(self):
        """测试存储邮件时更新邮箱计数"""
        # 先创建一个邮箱
        mailbox, _ = Mailbox.objects.using('mailserver_rw').get_or_create(
            account_id=self.test_account.id,
            path='INBOX',
            defaults={
                'name': 'INBOX',
                'message_count': 0,
                'unread_count': 0,
                'ct': int(time.time() * 1000),
                'dt': int(time.time() * 1000)
            }
        )
        
        # 存储多封邮件
        for i in range(3):
            msg = MIMEText(f'Email {i}', 'plain')
            msg['From'] = 'sender@example.com'
            msg['To'] = 'test@example.com'
            msg['Subject'] = f'Subject {i}'
            msg['Message-ID'] = f'<msg{i}@example.com>'
            
            self.storage_service.store_mail(
                account=self.test_account,
                mailbox_name='INBOX',
                email_data=msg.as_bytes()
            )
        
        # 验证邮箱计数已更新
        mailbox.refresh_from_db()
        self.assertEqual(mailbox.message_count, 3)
    
    def test_retrieve_mail_success(self):
        """测试检索邮件成功"""
        # 创建邮件和附件
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=1,  # 临时ID，实际测试中会创建邮箱
            message_id='<retrieve123@example.com>',
            subject='Retrieve Test',
            from_address='sender@example.com',
            to_addresses='test@example.com',
            text_body='Test body',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            dt=int(time.time() * 1000)
        )
        
        # 创建附件记录
        from app_mailserver.models.mail_attachment import MailAttachment
        MailAttachment.objects.using('mailserver_rw').create(
            message_id=message.id,
            filename='test.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/test.pdf',
            ct=int(time.time() * 1000)
        )
        
        result = self.storage_service.retrieve_mail(message.id)
        
        self.assertIsNotNone(result)
        self.assertIn('message', result)
        self.assertIn('attachments', result)
        self.assertEqual(result['message'].id, message.id)
        self.assertEqual(len(result['attachments']), 1)
        self.assertEqual(result['attachments'][0]['filename'], 'test.pdf')
    
    def test_retrieve_mail_not_found(self):
        """测试检索不存在的邮件"""
        result = self.storage_service.retrieve_mail(99999)
        self.assertIsNone(result)
    
    def test_get_attachment_data_success(self):
        """测试获取附件数据成功"""
        # 创建邮件和附件
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=1,
            message_id='<attach123@example.com>',
            subject='Test',
            from_address='sender@example.com',
            to_addresses='test@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            dt=int(time.time() * 1000)
        )
        
        from app_mailserver.models.mail_attachment import MailAttachment
        attachment = MailAttachment.objects.using('mailserver_rw').create(
            message_id=message.id,
            filename='test.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/test.pdf',
            ct=int(time.time() * 1000)
        )
        
        data = self.storage_service.get_attachment_data(attachment.id)
        
        self.assertIsNotNone(data)
        self.assertEqual(data, b'attachment data')
        # 验证调用了 OSS service
        self.mock_oss_service.download_attachment.assert_called_once_with('1/1/test.pdf')
    
    def test_get_attachment_data_not_found(self):
        """测试获取不存在的附件数据"""
        data = self.storage_service.get_attachment_data(99999)
        self.assertIsNone(data)
    
    def test_delete_mail_success(self):
        """测试删除邮件成功"""
        # 创建邮箱
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='INBOX',
            path='INBOX',
            message_count=1,
            unread_count=0,
            ct=int(time.time() * 1000),
            dt=int(time.time() * 1000)
        )
        
        # 创建邮件和附件
        message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=mailbox.id,
            message_id='<delete123@example.com>',
            subject='Delete Test',
            from_address='sender@example.com',
            to_addresses='test@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            dt=int(time.time() * 1000)
        )
        
        from app_mailserver.models.mail_attachment import MailAttachment
        attachment = MailAttachment.objects.using('mailserver_rw').create(
            message_id=message.id,
            filename='test.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/test.pdf',
            ct=int(time.time() * 1000)
        )
        
        result = self.storage_service.delete_mail(message.id)
        
        self.assertTrue(result)
        
        # 验证邮件已删除
        with self.assertRaises(MailMessage.DoesNotExist):
            MailMessage.objects.using('mailserver_rw').get(id=message.id)
        
        # 验证附件记录已删除
        with self.assertRaises(MailAttachment.DoesNotExist):
            MailAttachment.objects.using('mailserver_rw').get(id=attachment.id)
        
        # 验证 OSS service 被调用来删除附件
        self.mock_oss_service.delete_attachment.assert_called_once_with('1/1/test.pdf')
        
        # 验证邮箱计数已更新
        mailbox.refresh_from_db()
        self.assertEqual(mailbox.message_count, 0)
    
    def test_delete_mail_not_found(self):
        """测试删除不存在的邮件"""
        result = self.storage_service.delete_mail(99999)
        self.assertFalse(result)
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 正常文件名
        self.assertEqual(self.storage_service._sanitize_filename('document.pdf'), 'document.pdf')
        
        # 包含特殊字符
        self.assertEqual(self.storage_service._sanitize_filename('file with spaces.pdf'), 'file_with_spaces.pdf')
        self.assertEqual(self.storage_service._sanitize_filename('file/with/slashes.pdf'), 'file_with_slashes.pdf')
        
        # 超长文件名
        long_name = 'a' * 300 + '.pdf'
        sanitized = self.storage_service._sanitize_filename(long_name)
        self.assertLessEqual(len(sanitized), 255)
        self.assertTrue(sanitized.endswith('.pdf'))
    
    def test_generate_message_id(self):
        """测试生成消息ID"""
        message_id = self.storage_service._generate_message_id()
        
        self.assertTrue(message_id.startswith('<'))
        self.assertTrue(message_id.endswith('@mailserver>'))
        self.assertIn('@mailserver', message_id)
    
    def test_get_storage_service_singleton(self):
        """测试存储服务的单例模式"""
        service1 = get_storage_service()
        service2 = get_storage_service()
        
        # 应该是同一个实例
        self.assertIs(service1, service2)
    
    def test_store_email_without_message_id(self):
        """测试存储没有Message-ID的邮件（应该自动生成）"""
        msg = MIMEText('Test email without Message-ID.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'test@example.com'
        msg['Subject'] = 'No Message-ID'
        # 不设置 Message-ID
        
        email_data = msg.as_bytes()
        mail_message = self.storage_service.store_mail(
            account=self.test_account,
            mailbox_name='INBOX',
            email_data=email_data
        )
        
        # 应该自动生成 Message-ID
        self.assertIsNotNone(mail_message.message_id)
        self.assertTrue(mail_message.message_id.startswith('<'))
        self.assertTrue(mail_message.message_id.endswith('@mailserver>'))

