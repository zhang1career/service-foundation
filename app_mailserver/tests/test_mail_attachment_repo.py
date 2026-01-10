"""
单元测试：MailAttachment Repository

测试覆盖：
- create_mail_attachment
- get_attachment_by_id
- get_attachments_by_message
- delete_attachments_by_message
"""
import time
from django.test import TransactionTestCase

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_attachment import MailAttachment
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.repos.mail_attachment_repo import (
    create_mail_attachment,
    get_attachment_by_id,
    get_attachments_by_message,
    delete_attachments_by_message,
)
from common.enums.content_type_enum import ContentTypeEnum


class TestMailAttachmentRepo(TransactionTestCase):
    """测试 MailAttachment repository 函数"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前清理数据"""
        MailAccount.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailMessage.objects.using('mailserver_rw').all().delete()
        MailAttachment.objects.using('mailserver_rw').all().delete()

        # 创建测试账户、邮箱和邮件
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

        self.test_message = MailMessage.objects.using('mailserver_rw').create(
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

    def tearDown(self):
        """每个测试后清理数据"""
        MailAttachment.objects.using('mailserver_rw').all().delete()
        MailMessage.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()

    def test_create_mail_attachment_success(self):
        """测试创建邮件附件成功"""
        attachment = create_mail_attachment(
            message_id=self.test_message.id,
            filename='test.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/test.pdf',
            content_disposition='attachment',
            ct=int(time.time() * 1000)
        )

        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.filename, 'test.pdf')
        self.assertEqual(attachment.content_type, ContentTypeEnum.APPLICATION_PDF.value)
        self.assertEqual(attachment.size, 1024)
        self.assertEqual(attachment.oss_bucket, 'mail-attachments')
        self.assertEqual(attachment.oss_key, '1/1/test.pdf')

        # 验证数据库中已创建
        db_attachment = MailAttachment.objects.using('mailserver_rw').get(id=attachment.id)
        self.assertEqual(db_attachment.filename, 'test.pdf')

    def test_create_mail_attachment_with_inline(self):
        """测试创建内嵌附件（inline）"""
        attachment = create_mail_attachment(
            message_id=self.test_message.id,
            filename='image.jpg',
            content_type=ContentTypeEnum.IMAGE_JPEG.value,
            size=2048,
            oss_bucket='mail-attachments',
            oss_key='1/1/image.jpg',
            content_id='<cid123>',
            content_disposition='inline',
            ct=int(time.time() * 1000)
        )

        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.content_disposition, 'inline')
        self.assertEqual(attachment.content_id, '<cid123>')

    def test_get_attachment_by_id_success(self):
        """测试根据ID获取附件成功"""
        attachment = MailAttachment.objects.using('mailserver_rw').create(
            message_id=self.test_message.id,
            filename='test.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/test.pdf',
            ct=int(time.time() * 1000)
        )

        result = get_attachment_by_id(attachment.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, attachment.id)
        self.assertEqual(result.filename, 'test.pdf')

    def test_get_attachment_by_id_not_found(self):
        """测试获取不存在的附件"""
        result = get_attachment_by_id(99999)
        self.assertIsNone(result)

    def test_get_attachments_by_message_success(self):
        """测试获取邮件的所有附件"""
        # 创建多个附件
        att1 = MailAttachment.objects.using('mailserver_rw').create(
            message_id=self.test_message.id,
            filename='file1.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/file1.pdf',
            ct=int(time.time() * 1000)
        )
        att2 = MailAttachment.objects.using('mailserver_rw').create(
            message_id=self.test_message.id,
            filename='file2.jpg',
            content_type=ContentTypeEnum.IMAGE_JPEG.value,
            size=2048,
            oss_bucket='mail-attachments',
            oss_key='1/1/file2.jpg',
            ct=int(time.time() * 1000)
        )

        # 为另一个邮件创建附件（不应返回）
        other_message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<other@example.com>',
            subject='Other',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        MailAttachment.objects.using('mailserver_rw').create(
            message_id=other_message.id,
            filename='other.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/2/other.pdf',
            ct=int(time.time() * 1000)
        )

        result = get_attachments_by_message(self.test_message.id)

        self.assertEqual(len(result), 2)
        result_ids = {att.id for att in result}
        self.assertIn(att1.id, result_ids)
        self.assertIn(att2.id, result_ids)

    def test_get_attachments_by_message_empty(self):
        """测试获取没有附件的邮件的附件列表"""
        result = get_attachments_by_message(self.test_message.id)
        self.assertEqual(len(result), 0)

    def test_delete_attachments_by_message(self):
        """测试删除邮件的所有附件"""
        # 创建多个附件
        att1 = MailAttachment.objects.using('mailserver_rw').create(
            message_id=self.test_message.id,
            filename='file1.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/file1.pdf',
            ct=int(time.time() * 1000)
        )
        att2 = MailAttachment.objects.using('mailserver_rw').create(
            message_id=self.test_message.id,
            filename='file2.jpg',
            content_type=ContentTypeEnum.IMAGE_JPEG.value,
            size=2048,
            oss_bucket='mail-attachments',
            oss_key='1/1/file2.jpg',
            ct=int(time.time() * 1000)
        )

        # 为另一个邮件创建附件（不应被删除）
        other_message = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<other@example.com>',
            subject='Other',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )
        other_att = MailAttachment.objects.using('mailserver_rw').create(
            message_id=other_message.id,
            filename='other.pdf',
            content_type=ContentTypeEnum.APPLICATION_PDF.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/2/other.pdf',
            ct=int(time.time() * 1000)
        )

        # 删除测试邮件的所有附件
        count = delete_attachments_by_message(self.test_message.id)

        self.assertEqual(count, 2)

        # 验证附件已被删除
        with self.assertRaises(MailAttachment.DoesNotExist):
            MailAttachment.objects.using('mailserver_rw').get(id=att1.id)
        with self.assertRaises(MailAttachment.DoesNotExist):
            MailAttachment.objects.using('mailserver_rw').get(id=att2.id)

        # 验证其他邮件的附件仍然存在
        self.assertIsNotNone(MailAttachment.objects.using('mailserver_rw').get(id=other_att.id))

    def test_delete_attachments_by_message_empty(self):
        """测试删除没有附件的邮件的附件（应该返回0）"""
        count = delete_attachments_by_message(self.test_message.id)
        self.assertEqual(count, 0)

    def test_attachment_default_content_type(self):
        """测试附件的默认内容类型"""
        attachment = create_mail_attachment(
            message_id=self.test_message.id,
            filename='unknown.bin',
            content_type=ContentTypeEnum.APPLICATION_OCTET_STREAM.value,
            size=1024,
            oss_bucket='mail-attachments',
            oss_key='1/1/unknown.bin',
            ct=int(time.time() * 1000)
        )

        self.assertEqual(attachment.content_type, ContentTypeEnum.APPLICATION_OCTET_STREAM.value)
