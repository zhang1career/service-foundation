"""
单元测试：IMAP Server UID SEARCH 功能

测试覆盖：
- _parse_imap_date: 日期解析功能
- handle_uid_search: UID SEARCH 命令处理
  - SINCE 条件
  - UNSEEN 条件
  - 组合条件
"""
import asyncio
import time
from datetime import datetime, timezone
from django.test import TransactionTestCase
from unittest.mock import AsyncMock

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.servers.imap_server import IMAPHandler


class TestIMAPServerUIDSearch(TransactionTestCase):
    """测试 IMAP Server UID SEARCH 功能"""

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

    def _create_handler(self):
        """创建 IMAPHandler 实例（使用 mock 的 reader/writer）"""
        reader = AsyncMock()
        writer = AsyncMock()
        handler = IMAPHandler(reader, writer)
        handler.account = self.test_account
        handler.selected_mailbox = self.test_mailbox
        handler.authenticated = True
        return handler

    def _parse_imap_date(self, date_str: str) -> datetime:
        """测试辅助方法：解析 IMAP 日期"""
        handler = self._create_handler()
        return handler._parse_imap_date(date_str)

    def test_parse_imap_date_valid(self):
        """测试解析有效的 IMAP 日期格式"""
        date_str = "08-Jan-2026"
        result = self._parse_imap_date(date_str)

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 8)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_parse_imap_date_invalid_format(self):
        """测试解析无效的日期格式"""
        date_str = "2026-01-08"  # 错误的格式
        result = self._parse_imap_date(date_str)
        self.assertIsNone(result)

    def test_parse_imap_date_invalid_date(self):
        """测试解析无效的日期值"""
        date_str = "32-Jan-2026"  # 无效的日期
        result = self._parse_imap_date(date_str)
        self.assertIsNone(result)

    def test_parse_imap_date_different_months(self):
        """测试解析不同月份的日期"""
        test_cases = [
            ("01-Jan-2026", 1),
            ("15-Feb-2026", 2),
            ("28-Mar-2026", 3),
            ("30-Apr-2026", 4),
            ("31-May-2026", 5),
            ("01-Dec-2025", 12),
        ]

        for date_str, expected_month in test_cases:
            result = self._parse_imap_date(date_str)
            self.assertIsNotNone(result, f"Failed to parse: {date_str}")
            self.assertEqual(result.month, expected_month, f"Wrong month for: {date_str}")

    async def _run_uid_search_test(self, handler, args):
        """运行 UID SEARCH 测试的辅助方法"""
        responses = []
        original_send = handler.send_response

        async def capture_response(response):
            responses.append(response)
            # 调用原始的 send_response 方法
            await original_send(response)

        # 替换 send_response 方法
        handler.send_response = capture_response

        tag = "A001"
        await handler.handle_uid_search(tag, args)

        return responses

    def test_uid_search_since_condition(self):
        """测试 UID SEARCH SINCE 条件"""
        # 创建测试邮件，不同日期
        base_time = int(time.time() * 1000)

        # 2026-01-05 的邮件（早于搜索日期）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 2026-01-08 的邮件（等于搜索日期）
        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 2026-01-10 的邮件（晚于搜索日期）
        msg3 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg3@example.com>',
            subject='Message 3',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            mt=int(datetime(2026, 1, 10, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['SINCE', '08-Jan-2026']

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 验证响应
        self.assertEqual(len(responses), 2)  # SEARCH 响应 + OK 响应

        search_response = responses[0]
        self.assertTrue(search_response.startswith('* SEARCH'))

        # 应该包含 msg2 和 msg3 的 ID（>= 2026-01-08）
        uids = search_response.replace('* SEARCH', '').strip().split()
        self.assertIn(str(msg2.id), uids)
        self.assertIn(str(msg3.id), uids)
        self.assertNotIn(str(msg1.id), uids)  # msg1 应该不在结果中

        ok_response = responses[1]
        self.assertTrue(ok_response.startswith('A001 OK'))

    def test_uid_search_unseen_condition(self):
        """测试 UID SEARCH UNSEEN 条件"""
        # 创建已读和未读邮件
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<read1@example.com>',
            subject='Read Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=True,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<unread1@example.com>',
            subject='Unread Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg3 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<unread2@example.com>',
            subject='Unread Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['UNSEEN']

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 验证响应
        self.assertEqual(len(responses), 2)

        search_response = responses[0]
        self.assertTrue(search_response.startswith('* SEARCH'))

        uids = search_response.replace('* SEARCH', '').strip().split()
        self.assertIn(str(msg2.id), uids)
        self.assertIn(str(msg3.id), uids)
        self.assertNotIn(str(msg1.id), uids)  # 已读邮件不应在结果中

    def test_uid_search_combined_conditions(self):
        """测试 UID SEARCH 组合条件（SINCE + UNSEEN）"""
        base_time = int(time.time() * 1000)

        # 2026-01-05 的未读邮件（早于搜索日期，不应匹配）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 2026-01-08 的未读邮件（匹配条件）
        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 2026-01-10 的已读邮件（日期匹配但已读，不应匹配）
        msg3 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg3@example.com>',
            subject='Message 3',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=True,
            mt=int(datetime(2026, 1, 10, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 2026-01-10 的未读邮件（匹配条件）
        msg4 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg4@example.com>',
            subject='Message 4',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(datetime(2026, 1, 10, tzinfo=timezone.utc).timestamp() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['SINCE', '08-Jan-2026', 'UNSEEN']

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 验证响应
        self.assertEqual(len(responses), 2)

        search_response = responses[0]
        self.assertTrue(search_response.startswith('* SEARCH'))

        uids = search_response.replace('* SEARCH', '').strip().split()
        # 应该只包含 msg2 和 msg4（日期 >= 2026-01-08 且未读）
        self.assertIn(str(msg2.id), uids)
        self.assertIn(str(msg4.id), uids)
        self.assertNotIn(str(msg1.id), uids)  # 日期太早
        self.assertNotIn(str(msg3.id), uids)  # 已读

    def test_uid_search_empty_result(self):
        """测试 UID SEARCH 无匹配结果"""
        handler = self._create_handler()
        args = ['SINCE', '01-Jan-2099']  # 未来的日期，应该没有匹配

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 验证响应
        self.assertEqual(len(responses), 2)

        search_response = responses[0]
        self.assertEqual(search_response, '* SEARCH')  # 空结果

        ok_response = responses[1]
        self.assertTrue(ok_response.startswith('A001 OK'))

    def test_uid_search_invalid_date(self):
        """测试 UID SEARCH 无效日期格式"""
        handler = self._create_handler()
        args = ['SINCE', 'invalid-date']

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 应该返回错误响应
        self.assertEqual(len(responses), 1)
        self.assertTrue('BAD' in responses[0])
        self.assertTrue('Invalid date format' in responses[0])

    def test_uid_search_missing_date(self):
        """测试 UID SEARCH SINCE 缺少日期参数"""
        handler = self._create_handler()
        args = ['SINCE']  # 缺少日期

        responses = asyncio.run(self._run_uid_search_test(handler, args))

        # 应该返回错误响应
        self.assertEqual(len(responses), 1)
        self.assertTrue('BAD' in responses[0])
        self.assertTrue('SINCE requires a date' in responses[0])
