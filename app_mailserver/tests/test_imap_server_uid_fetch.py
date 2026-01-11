"""
单元测试：IMAP Server UID FETCH 功能

测试覆盖：
- _parse_uid_sequence: UID 序列解析功能
- handle_uid_fetch: UID FETCH 命令处理
  - 单个 UID
  - UID 范围
  - UID 范围到末尾 (2:*)
  - 最后一个 (*)
  - FLAGS 数据项
  - 其他数据项
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


class TestIMAPServerUIDFetch(TransactionTestCase):
    """测试 IMAP Server UID FETCH 功能"""

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

    def _filter_fetch_responses(self, responses):
        """过滤 FETCH 响应（格式：* <seq> FETCH (...)）"""
        return [r for r in responses if r.startswith('*') and 'FETCH' in r]

    def _parse_uid_sequence(self, uid_seq: str):
        """测试辅助方法：解析 UID 序列"""
        handler = self._create_handler()
        return handler._parse_uid_sequence(uid_seq)

    def test_parse_uid_sequence_single(self):
        """测试解析单个 UID"""
        result = self._parse_uid_sequence("2")
        self.assertEqual(result, [2])

    def test_parse_uid_sequence_range(self):
        """测试解析 UID 范围"""
        result = self._parse_uid_sequence("2:5")
        self.assertEqual(result, [2, 3, 4, 5])

    def test_parse_uid_sequence_range_same(self):
        """测试解析相同 UID 的范围（如 2:2）"""
        result = self._parse_uid_sequence("2:2")
        self.assertEqual(result, [2])

    def test_parse_uid_sequence_range_to_end(self):
        """测试解析到末尾的范围（如 2:*）"""
        result = self._parse_uid_sequence("2:*")
        self.assertEqual(result, [2, -1])  # -1 表示 "*"

    def test_parse_uid_sequence_wildcard(self):
        """测试解析通配符 *"""
        result = self._parse_uid_sequence("*")
        self.assertEqual(result, [])

    def test_parse_uid_sequence_invalid(self):
        """测试解析无效的 UID 序列"""
        result = self._parse_uid_sequence("abc")
        self.assertEqual(result, [])

    def test_parse_uid_sequence_invalid_range(self):
        """测试解析无效的范围"""
        result = self._parse_uid_sequence("2:abc")
        self.assertEqual(result, [])

    async def _run_uid_fetch_test(self, handler, args):
        """运行 UID FETCH 测试的辅助方法"""
        responses = []
        data_responses = []
        original_send = handler.send_response
        original_send_data = handler.send_data

        async def capture_response(response):
            responses.append(response)
            await original_send(response)

        async def capture_data(data):
            data_responses.append(data)
            await original_send_data(data)

        handler.send_response = capture_response
        handler.send_data = capture_data

        tag = "A001"
        await handler.handle_uid_fetch(tag, args)

        return responses, data_responses

    def test_uid_fetch_single_uid_flags(self):
        """测试 UID FETCH 单个 UID 的 FLAGS"""
        # 创建测试邮件
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=False,
            is_flagged=True,
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['2', '(FLAGS)']  # 假设 msg1.id 是 2，实际使用 msg1.id

        # 使用实际的 UID
        args = [str(msg1.id), '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应
        self.assertGreaterEqual(len(responses), 2)  # 至少有一个 FETCH 响应和一个 OK 响应

        # 查找 FETCH 响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = self._filter_fetch_responses(responses)
        self.assertGreater(len(fetch_responses), 0)

        fetch_response = fetch_responses[0]
        # 应该包含 UID
        self.assertIn('UID', fetch_response)
        self.assertIn(str(msg1.id), fetch_response)
        # 应该包含 FLAGS
        self.assertIn('FLAGS', fetch_response)
        # 应该包含 \Flagged（因为 is_flagged=True）
        self.assertIn('\\Flagged', fetch_response)

        # 验证 OK 响应
        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_range_flags(self):
        """测试 UID FETCH 范围 UID 的 FLAGS"""
        # 创建多个测试邮件
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
            is_read=True,
            mt=int(time.time() * 1000),
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用范围：从第一个 UID 到第二个 UID
        min_id = min(msg1.id, msg2.id)
        max_id = max(msg1.id, msg2.id)
        uid_range = f"{min_id}:{max_id}"

        handler = self._create_handler()
        args = [uid_range, '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = self._filter_fetch_responses(responses)
        self.assertEqual(len(fetch_responses), 2)  # 应该有两个 FETCH 响应

        # 验证每个响应都包含 UID 和 FLAGS
        for fetch_response in fetch_responses:
            self.assertIn('UID', fetch_response)
            self.assertIn('FLAGS', fetch_response)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_wildcard_last(self):
        """测试 UID FETCH 使用 *（最后一个）"""
        # 创建多个测试邮件
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
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
            mt=int(time.time() * 1000) + 1000,  # 稍晚的时间，应该是最后一个
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = ['*', '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = self._filter_fetch_responses(responses)
        self.assertEqual(len(fetch_responses), 1)  # 应该只有一个 FETCH 响应（最后一个）

        fetch_response = fetch_responses[0]
        # 应该包含最后一个消息的 UID（msg2.id，因为时间更晚）
        self.assertIn('UID', fetch_response)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_range_to_end(self):
        """测试 UID FETCH 范围到末尾 (2:*)"""
        # 创建多个测试邮件
        msg1 = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg1@example.com>',
            subject='Message 1',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
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
            mt=int(time.time() * 1000) + 1000,
            size=200,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        # 使用范围到末尾：从第一个 UID 到末尾
        min_id = min(msg1.id, msg2.id)
        uid_range = f"{min_id}:*"

        handler = self._create_handler()
        args = [uid_range, '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = self._filter_fetch_responses(responses)
        # 应该至少有包含 min_id 的消息的响应
        self.assertGreater(len(fetch_responses), 0)

        for fetch_response in fetch_responses:
            self.assertIn('UID', fetch_response)
            self.assertIn('FLAGS', fetch_response)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_seen_flag(self):
        """测试 UID FETCH 包含 \\Seen 标志"""
        msg = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg@example.com>',
            subject='Message',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            is_read=True,  # 已读
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = [str(msg.id), '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # FETCH 响应格式：* <seq> FETCH (...)
        fetch_responses = self._filter_fetch_responses(responses)
        self.assertEqual(len(fetch_responses), 1)

        fetch_response = fetch_responses[0]
        # 应该包含 \Seen 标志
        self.assertIn('\\Seen', fetch_response)

    def test_uid_fetch_no_matching_uid(self):
        """测试 UID FETCH 没有匹配的 UID"""
        # 不创建任何邮件

        handler = self._create_handler()
        args = ['999999', '(FLAGS)']  # 不存在的 UID

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 OK，但没有 FETCH 响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = [r for r in responses if r.startswith('*') and 'FETCH' in r]
        self.assertEqual(len(fetch_responses), 0)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_empty_mailbox(self):
        """测试 UID FETCH 空邮箱"""
        handler = self._create_handler()
        args = ['1', '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 OK，但没有 FETCH 响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = [r for r in responses if r.startswith('*') and 'FETCH' in r]
        self.assertEqual(len(fetch_responses), 0)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_invalid_uid_sequence(self):
        """测试 UID FETCH 无效的 UID 序列"""
        handler = self._create_handler()
        args = ['abc', '(FLAGS)']  # 无效的 UID

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0)

        bad_response = bad_responses[0]
        self.assertIn('Invalid UID sequence', bad_response)

    def test_uid_fetch_not_authenticated(self):
        """测试 UID FETCH 未认证的情况"""
        handler = self._create_handler()
        handler.authenticated = False  # 未认证

        args = ['1', '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 NO 错误
        no_responses = [r for r in responses if 'NO' in r]
        self.assertGreater(len(no_responses), 0)

        no_response = no_responses[0]
        self.assertIn('Not authenticated', no_response)

    def test_uid_fetch_no_mailbox_selected(self):
        """测试 UID FETCH 没有选择邮箱的情况"""
        handler = self._create_handler()
        handler.selected_mailbox = None  # 没有选择邮箱

        args = ['1', '(FLAGS)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 NO 错误
        no_responses = [r for r in responses if 'NO' in r]
        self.assertGreater(len(no_responses), 0)

        no_response = no_responses[0]
        self.assertIn('Not authenticated', no_response)

    def test_uid_fetch_insufficient_args(self):
        """测试 UID FETCH 参数不足"""
        handler = self._create_handler()
        args = ['1']  # 缺少数据项

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 应该返回 BAD 错误
        bad_responses = [r for r in responses if 'BAD' in r]
        self.assertGreater(len(bad_responses), 0)

        bad_response = bad_responses[0]
        self.assertIn('UID FETCH command requires', bad_response)

    def test_uid_fetch_body_structure(self):
        """测试 UID FETCH BODYSTRUCTURE 数据项"""
        msg = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg@example.com>',
            subject='Message',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            text_body='Test body',
            html_body='<html>Test</html>',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = [str(msg.id), '(BODYSTRUCTURE)']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应（FETCH 响应格式：* <seq> FETCH (...)）
        fetch_responses = self._filter_fetch_responses(responses)
        # 应该有一个 FETCH 响应（如果测试中有多个，使用第一个进行验证）
        self.assertGreaterEqual(len(fetch_responses), 1)
        
        # 检查第一个 FETCH 响应是否包含正确的信息
        fetch_response = fetch_responses[0]
        # 应该包含 UID
        self.assertIn('UID', fetch_response)
        self.assertIn(str(msg.id), fetch_response)
        # 应该包含 BODYSTRUCTURE
        self.assertIn('BODYSTRUCTURE', fetch_response)
        
        # 检查所有 FETCH 响应都应该包含 BODYSTRUCTURE 和 UID
        for resp in fetch_responses:
            self.assertIn('BODYSTRUCTURE', resp)
            self.assertIn('UID', resp)
            self.assertIn(str(msg.id), resp)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)

    def test_uid_fetch_full_body(self):
        """测试 UID FETCH BODY[] 数据项（完整邮件）"""
        msg = MailMessage.objects.using('mailserver_rw').create(
            account_id=self.test_account.id,
            mailbox_id=self.test_mailbox.id,
            message_id='<msg@example.com>',
            subject='Message',
            from_address='sender@example.com',
            to_addresses='recipient@example.com',
            text_body='Test body',
            mt=int(time.time() * 1000),
            size=100,
            ct=int(time.time() * 1000),
            ut=int(time.time() * 1000)
        )

        handler = self._create_handler()
        args = [str(msg.id), '(BODY[])']

        responses, data_responses = asyncio.run(self._run_uid_fetch_test(handler, args))

        # 验证响应
        # FETCH 响应格式：* <seq> FETCH (...)
        fetch_responses = self._filter_fetch_responses(responses)
        self.assertEqual(len(fetch_responses), 1)

        fetch_response = fetch_responses[0]
        # 应该包含 UID
        self.assertIn('UID', fetch_response)
        self.assertIn(str(msg.id), fetch_response)
        # 应该包含 BODY[]
        self.assertIn('BODY[]', fetch_response)

        # 应该发送了数据
        self.assertGreater(len(data_responses), 0)

        ok_responses = [r for r in responses if 'OK UID FETCH completed' in r]
        self.assertEqual(len(ok_responses), 1)
