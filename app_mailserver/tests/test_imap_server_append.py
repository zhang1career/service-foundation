r"""
单元测试：IMAP Server APPEND 功能

测试覆盖：
- handle_append: APPEND 命令处理
  - 基本 APPEND 命令（quoted string 格式）
  - 带 flags 的 APPEND（\Seen 等）
  - 带 date-time 的 APPEND
  - literal 格式的消息（{size}\r\n...）
  - 创建新邮箱
  - 错误情况（未认证、缺少参数等）

根据 IMAP 规范 RFC 3501：
- APPEND mailbox [flags] [date-time] message
- message 可以是 quoted string 或 literal ({size}\r\n...)
"""
import asyncio
import time
import uuid
from django.test import TransactionTestCase
from unittest.mock import AsyncMock

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.repos.mailbox_repo import get_mailbox_by_account_and_path
from app_mailserver.servers.imap_server import IMAPHandler


class TestIMAPServerAppend(TransactionTestCase):
    """测试 IMAP Server APPEND 功能"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前清理数据"""
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
            ut=int(time.time() * 1000)
        )

    def tearDown(self):
        """每个测试后清理数据"""
        MailMessage.objects.using('mailserver_rw').all().delete()
        Mailbox.objects.using('mailserver_rw').all().delete()
        MailAccount.objects.using('mailserver_rw').all().delete()

    def _create_handler(self):
        """创建 IMAPHandler 实例（使用 mock 的 reader/writer）"""
        reader = AsyncMock()
        writer = AsyncMock()
        handler = IMAPHandler(reader, writer)
        handler.account = self.test_account
        handler.authenticated = True
        return handler

    def _create_test_email(self, message_id: str = None) -> str:
        """创建测试邮件内容（RFC 822 格式）
        
        Args:
            message_id: 可选的 Message-ID，如果不提供则使用默认值
        """
        if message_id is None:
            message_id = '<test@example.com>'
        return f"""Message-ID: {message_id}
From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Mon, 01 Jan 2024 12:00:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Test message body."""

    async def _run_append_test(self, handler, args, command_line, literal_data=None):
        """
        运行 APPEND 测试的辅助方法
        
        Args:
            handler: IMAPHandler 实例
            args: 命令参数列表
            command_line: 完整命令字符串
            literal_data: 如果是 literal 格式，这里传入要读取的数据（bytes）
        """
        responses = []
        original_send = handler.send_response

        async def capture_response(response):
            responses.append(response)
            await original_send(response)

        handler.send_response = capture_response

        # 如果提供了 literal_data，设置 reader.readexactly 和 readline 的 mock
        if literal_data is not None:
            async def mock_readexactly(size):
                return literal_data

            handler.reader.readexactly = mock_readexactly

            async def mock_readline():
                return b'\r\n'

            handler.reader.readline = mock_readline

        tag = "A001"
        await handler.handle_append(tag, args, command_line)

        return responses

    def test_append_basic_quoted_string(self):
        """测试基本的 APPEND 命令（quoted string 格式）"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent', f'"{email_content}"']
        command_line = f'A001 APPEND Sent "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1, f"Expected OK response, got: {responses}")

        # 验证消息已保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.from_address, 'sender@example.com')

        # 验证邮箱已创建
        mailbox = get_mailbox_by_account_and_path(self.test_account.id, 'Sent')
        self.assertIsNotNone(mailbox)
        self.assertEqual(mailbox.path, 'Sent')

    def test_append_with_flags_seen(self):
        r"""测试带 \Seen flag 的 APPEND 命令"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent', '(\\Seen)', f'"{email_content}"']
        command_line = f'A001 APPEND Sent (\\Seen) "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存且标记为已读
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertTrue(message.is_read)

    def test_append_with_flags_unseen(self):
        r"""测试不带 \Seen flag 的 APPEND 命令（默认未读）"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent', f'"{email_content}"']
        command_line = f'A001 APPEND Sent "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存且未读
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertFalse(message.is_read)

    def test_append_with_date_time(self):
        """测试带 date-time 的 APPEND 命令"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        date_str = '"01-Jan-2024 12:00:00 +0000"'
        args = ['Sent', date_str, f'"{email_content}"']
        command_line = f'A001 APPEND Sent {date_str} "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

    def test_append_with_flags_and_date_time(self):
        """测试带 flags 和 date-time 的 APPEND 命令"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        date_str = '"01-Jan-2024 12:00:00 +0000"'
        args = ['Sent', '(\\Seen)', date_str, f'"{email_content}"']
        command_line = f'A001 APPEND Sent (\\Seen) {date_str} "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存且标记为已读
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertTrue(message.is_read)

    def test_append_literal_format(self):
        """测试 literal 格式的 APPEND 命令（{size}\r\n...）"""
        email_content = self._create_test_email()
        email_bytes = email_content.encode('utf-8')
        literal_size = len(email_bytes)

        handler = self._create_handler()
        args = ['Sent']
        command_line = f'A001 APPEND Sent {{{literal_size}}}'

        responses = asyncio.run(
            self._run_append_test(handler, args, command_line, literal_data=email_bytes)
        )

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertEqual(message.subject, 'Test Subject')

    def test_append_literal_with_flags(self):
        """测试带 flags 的 literal 格式 APPEND 命令"""
        email_content = self._create_test_email()
        email_bytes = email_content.encode('utf-8')
        literal_size = len(email_bytes)

        handler = self._create_handler()
        args = ['Sent', '(\\Seen)']
        command_line = f'A001 APPEND Sent (\\Seen) {{{literal_size}}}'

        responses = asyncio.run(
            self._run_append_test(handler, args, command_line, literal_data=email_bytes)
        )

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存且标记为已读
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertTrue(message.is_read)

    def test_append_creates_mailbox(self):
        """测试 APPEND 命令自动创建不存在的邮箱"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent', f'"{email_content}"']
        command_line = f'A001 APPEND Sent "{email_content}"'

        # 验证邮箱不存在
        mailbox_before = get_mailbox_by_account_and_path(self.test_account.id, 'Sent')
        self.assertIsNone(mailbox_before)

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证邮箱已创建
        mailbox_after = get_mailbox_by_account_and_path(self.test_account.id, 'Sent')
        self.assertIsNotNone(mailbox_after)
        self.assertEqual(mailbox_after.path, 'Sent')
        self.assertEqual(mailbox_after.name, 'Sent')

    def test_append_existing_mailbox(self):
        """测试 APPEND 命令使用已存在的邮箱"""
        # 创建邮箱
        mailbox = Mailbox.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            name='Sent',
            path='Sent',
            message_count=0,
            unread_count=0,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent', f'"{email_content}"']
        command_line = f'A001 APPEND Sent "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存到现有邮箱
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id,
            mailbox_id=mailbox.id
        )
        self.assertEqual(messages.count(), 1)

    def test_append_not_authenticated(self):
        """测试未认证时的 APPEND 命令"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        handler.authenticated = False  # 未认证

        args = ['Sent', f'"{email_content}"']
        command_line = f'A001 APPEND Sent "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证返回 NO 错误
        no_responses = [r for r in responses if 'NO' in r and 'Not authenticated' in r]
        self.assertGreater(len(no_responses), 0, f"Expected NO response, got: {responses}")

        # 验证消息未保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 0)

    def test_append_missing_mailbox_name(self):
        """测试缺少邮箱名称的 APPEND 命令（空参数列表）"""
        handler = self._create_handler()
        args = []  # 空参数列表，缺少邮箱名称
        command_line = 'A001 APPEND'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0, f"Expected BAD response, got: {responses}")

        bad_response = bad_responses[0]
        self.assertIn('requires mailbox name', bad_response)

    def test_append_missing_message_data_quoted(self):
        """测试缺少消息数据的 APPEND 命令（quoted string 格式）"""
        handler = self._create_handler()
        args = ['Sent']  # 缺少消息数据
        command_line = 'A001 APPEND Sent'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0)

        bad_response = bad_responses[0]
        self.assertIn('requires message data', bad_response)

    def test_append_multiple_messages(self):
        """测试多次 APPEND 命令保存多条消息"""
        # 第一条消息 - 使用唯一的 Message-ID
        email1 = self._create_test_email(message_id=f'<test1-{uuid.uuid4()}@example.com>').replace('Test Subject',
                                                                                                   'Subject 1')
        handler1 = self._create_handler()
        args1 = ['Sent', f'"{email1}"']
        command_line1 = f'A001 APPEND Sent "{email1}"'
        responses1 = asyncio.run(self._run_append_test(handler1, args1, command_line1))

        ok_responses1 = [r for r in responses1 if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses1), 1, f"First append failed, responses: {responses1}")

        # 第二条消息 - 使用新的 handler 和唯一的 Message-ID
        email2 = self._create_test_email(message_id=f'<test2-{uuid.uuid4()}@example.com>').replace('Test Subject',
                                                                                                   'Subject 2')
        handler2 = self._create_handler()
        args2 = ['Sent', f'"{email2}"']
        command_line2 = f'A002 APPEND Sent "{email2}"'
        responses2 = asyncio.run(self._run_append_test(handler2, args2, command_line2))

        ok_responses2 = [r for r in responses2 if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses2), 1, f"Second append failed, responses: {responses2}")

        # 验证两条消息都已保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        ).order_by('ct')
        self.assertEqual(messages.count(), 2)

        self.assertEqual(messages[0].subject, 'Subject 1')
        self.assertEqual(messages[1].subject, 'Subject 2')

    def test_append_nested_mailbox_path(self):
        """测试嵌套邮箱路径（如 Sent.Items）"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['Sent.Items', f'"{email_content}"']
        command_line = f'A001 APPEND Sent.Items "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证邮箱已创建（name 应该是最后一部分）
        mailbox = get_mailbox_by_account_and_path(self.test_account.id, 'Sent.Items')
        self.assertIsNotNone(mailbox)
        self.assertEqual(mailbox.path, 'Sent.Items')
        self.assertEqual(mailbox.name, 'Items')

    def test_append_quoted_mailbox_name(self):
        """测试带引号的邮箱名称"""
        email_content = self._create_test_email()
        handler = self._create_handler()
        args = ['"Sent"', f'"{email_content}"']
        command_line = f'A001 APPEND "Sent" "{email_content}"'

        responses = asyncio.run(self._run_append_test(handler, args, command_line))

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证邮箱已创建
        mailbox = get_mailbox_by_account_and_path(self.test_account.id, 'Sent')
        self.assertIsNotNone(mailbox)

    def test_append_large_message_literal(self):
        """测试大的 literal 消息"""
        # 创建较大的邮件内容
        large_body = 'X' * 10000
        email_content = f"""Message-ID: <large@example.com>
From: sender@example.com
To: recipient@example.com
Subject: Large Message
Date: Mon, 01 Jan 2024 12:00:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

{large_body}"""

        email_bytes = email_content.encode('utf-8')
        literal_size = len(email_bytes)

        handler = self._create_handler()
        args = ['Sent']
        command_line = f'A001 APPEND Sent {{{literal_size}}}'

        responses = asyncio.run(
            self._run_append_test(handler, args, command_line, literal_data=email_bytes)
        )

        # 验证响应
        ok_responses = [r for r in responses if 'OK APPEND completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已保存
        messages = MailMessage.objects.using('mailserver_rw').filter(
            account_id=self.test_account.id
        )
        self.assertEqual(messages.count(), 1)

        message = messages.first()
        self.assertEqual(message.subject, 'Large Message')
        self.assertIn(large_body, message.text_body)
