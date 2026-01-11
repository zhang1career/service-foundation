"""
单元测试：IMAP Server UID STORE 功能

测试覆盖：
- handle_uid_store: UID STORE 命令处理
  - 单个 UID
  - UID 范围
  - UID 范围到末尾 (2:*)
  - 最后一个 (*)
  - +FLAGS \\Seen (标记为已读)
  - -FLAGS \\Seen (取消已读标记)
  - 错误情况
"""
import asyncio
import time
from django.test import TransactionTestCase
from unittest.mock import AsyncMock

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.servers.imap_server import IMAPHandler


class TestIMAPServerUIDStore(TransactionTestCase):
    """测试 IMAP Server UID STORE 功能"""

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

    async def _run_uid_store_test(self, handler, args):
        """运行 UID STORE 测试的辅助方法"""
        responses = []
        original_send = handler.send_response

        async def capture_response(response):
            responses.append(response)
            await original_send(response)

        handler.send_response = capture_response

        tag = "A001"
        await handler.handle_uid_store(tag, args)

        return responses

    def test_uid_store_single_uid_add_seen_flag(self):
        """测试 UID STORE 单个 UID 的 +FLAGS \\Seen"""
        # 创建测试邮件（未读）
        msg = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg@example.com>',
            subject='Message',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = [str(msg.id), '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已被标记为已读
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_uid_store_single_uid_remove_seen_flag(self):
        """测试 UID STORE 单个 UID 的 -FLAGS \\Seen"""
        # 创建测试邮件（已读）
        msg = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg@example.com>',
            subject='Message',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=True,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = [str(msg.id), '-FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证消息已被标记为未读
        msg.refresh_from_db()
        self.assertFalse(msg.is_read)

    def test_uid_store_range_add_seen_flag(self):
        """测试 UID STORE UID 范围的 +FLAGS \\Seen"""
        # 创建多个测试邮件（未读）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用范围：从第一个 UID 到第二个 UID
        min_id = min(msg1.id, msg2.id)
        max_id = max(msg1.id, msg2.id)
        uid_range = f"{min_id}:{max_id}"

        handler = self._create_handler()
        args = [uid_range, '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证所有消息都被标记为已读
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        self.assertTrue(msg1.is_read)
        self.assertTrue(msg2.is_read)

    def test_uid_store_wildcard_last(self):
        """测试 UID STORE 使用 *（最后一个）"""
        # 创建多个测试邮件（未读）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['*', '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证最后一个消息被标记为已读（msg2，因为时间更晚）
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        self.assertFalse(msg1.is_read)  # 第一个消息应该未被标记
        self.assertTrue(msg2.is_read)  # 最后一个消息应该被标记

    def test_uid_store_range_to_end(self):
        """测试 UID STORE 范围到末尾 (2:*)"""
        # 创建多个测试邮件（未读）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用范围到末尾：从第一个 UID 到末尾
        min_id = min(msg1.id, msg2.id)
        uid_range = f"{min_id}:*"

        handler = self._create_handler()
        args = [uid_range, '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证所有从 min_id 开始的消息都被标记为已读
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        self.assertTrue(msg1.is_read)
        self.assertTrue(msg2.is_read)

    def test_uid_store_no_matching_uid(self):
        """测试 UID STORE 没有匹配的 UID"""
        # 不创建任何邮件

        handler = self._create_handler()
        args = ['999999', '+FLAGS', '(\\Seen)']  # 不存在的 UID

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 OK，但没有实际更新
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_store_empty_mailbox(self):
        """测试 UID STORE 空邮箱"""
        handler = self._create_handler()
        args = ['1', '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 OK，但没有实际更新
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_store_invalid_uid_sequence(self):
        """测试 UID STORE 无效的 UID 序列"""
        handler = self._create_handler()
        args = ['abc', '+FLAGS', '(\\Seen)']  # 无效的 UID

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0)

        bad_response = bad_responses[0]
        self.assertIn('Invalid UID sequence', bad_response)

    def test_uid_store_not_authenticated(self):
        """测试 UID STORE 未认证的情况"""
        handler = self._create_handler()
        handler.authenticated = False  # 未认证

        args = ['1', '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 NO 错误
        no_responses = [r for r in responses if 'NO' in r]
        self.assertGreater(len(no_responses), 0)

        no_response = no_responses[0]
        self.assertIn('Not authenticated', no_response)

    def test_uid_store_no_mailbox_selected(self):
        """测试 UID STORE 没有选择邮箱的情况"""
        handler = self._create_handler()
        handler.selected_mailbox = None  # 没有选择邮箱

        args = ['1', '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 NO 错误
        no_responses = [r for r in responses if 'NO' in r]
        self.assertGreater(len(no_responses), 0)

        no_response = no_responses[0]
        self.assertIn('Not authenticated', no_response)

    def test_uid_store_insufficient_args(self):
        """测试 UID STORE 参数不足"""
        handler = self._create_handler()
        args = ['1']  # 缺少 flags

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 应该返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0)

        bad_response = bad_responses[0]
        self.assertIn('UID STORE command requires', bad_response)

    def test_uid_store_comma_separated_uids(self):
        """测试 UID STORE 使用逗号分隔的 UID 列表"""
        # 创建多个测试邮件（未读）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg3 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg3@example.com>',
            subject='Message 3',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 2000,
            size=300,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用逗号分隔的 UID 列表
        uid_list = f"{msg1.id},{msg2.id},{msg3.id}"

        handler = self._create_handler()
        args = [uid_list, '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证所有消息都被标记为已读
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        msg3.refresh_from_db()
        self.assertTrue(msg1.is_read)
        self.assertTrue(msg2.is_read)
        self.assertTrue(msg3.is_read)

    def test_uid_store_comma_separated_with_range(self):
        """测试 UID STORE 使用混合格式：逗号分隔和范围（如 1,2:5,7）"""
        # 创建多个测试邮件（未读）
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg2 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg2@example.com>',
            subject='Message 2',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        msg3 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg3@example.com>',
            subject='Message 3',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            mt=int(time.time() * 1000) + 2000,
            size=300,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用混合格式：单个 UID，范围，单个 UID
        min_id = min(msg1.id, msg2.id, msg3.id)
        max_id = max(msg1.id, msg2.id, msg3.id)
        mid_id = sorted([msg1.id, msg2.id, msg3.id])[1]

        # 格式：第一个UID,范围,最后一个UID
        uid_sequence = f"{min_id},{min_id}:{mid_id},{max_id}"

        handler = self._create_handler()
        args = [uid_sequence, '+FLAGS', '(\\Seen)']

        responses = asyncio.run(self._run_uid_store_test(handler, args))

        # 验证响应
        ok_responses = [r for r in responses if 'OK UID STORE completed' in r]
        self.assertEqual(len(ok_responses), 1)

        # 验证所有匹配的消息都被标记为已读
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        msg3.refresh_from_db()
        self.assertTrue(msg1.is_read)
        self.assertTrue(msg2.is_read)
        self.assertTrue(msg3.is_read)

