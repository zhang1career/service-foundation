"""
单元测试：MailParser 邮件解析服务

测试覆盖：
- parse_email (简单邮件、多部分邮件、带附件)
- _extract_body_and_attachments
- _extract_attachment
- _get_extension_from_content_type
"""
from email import encoders
from unittest import TestCase

from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app_mailserver.services.mail_parser import MailParser


class TestMailParser(TestCase):
    """测试 MailParser 服务"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        self.parser = MailParser()

    def test_parse_simple_text_email(self):
        """测试解析简单文本邮件"""
        msg = MIMEText('This is a test email body.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Subject'
        msg['Message-ID'] = '<test123@example.com>'
        msg['Date'] = 'Mon, 1 Jan 2024 12:00:00 +0000'

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertEqual(result['from_address'], 'sender@example.com')
        self.assertEqual(result['to_addresses'], 'recipient@example.com')
        self.assertEqual(result['subject'], 'Test Subject')
        self.assertEqual(result['message_id'], '<test123@example.com>')
        self.assertIn('This is a test email body.', result['text_body'])
        self.assertEqual(result['html_body'], '')
        self.assertEqual(len(result['attachments']), 0)
        self.assertIsInstance(result['date'], datetime)

    def test_parse_html_email(self):
        """测试解析HTML邮件"""
        msg = MIMEText('<html><body><h1>Hello</h1></body></html>', 'html')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'HTML Email'
        msg['Message-ID'] = '<html123@example.com>'

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertIn('<html>', result['html_body'])
        self.assertEqual(result['text_body'], '')
        self.assertEqual(len(result['attachments']), 0)

    def test_parse_multipart_email_with_text_and_html(self):
        """测试解析包含文本和HTML的多部分邮件"""
        msg = MIMEMultipart('alternative')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Multipart Email'
        msg['Message-ID'] = '<multipart123@example.com>'

        text_part = MIMEText('This is plain text.', 'plain')
        html_part = MIMEText('<html><body>This is HTML.</body></html>', 'html')

        msg.attach(text_part)
        msg.attach(html_part)

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertIn('This is plain text.', result['text_body'])
        self.assertIn('This is HTML.', result['html_body'])
        self.assertEqual(len(result['attachments']), 0)

    def test_parse_email_with_attachment(self):
        """测试解析带附件的邮件"""
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Email with Attachment'
        msg['Message-ID'] = '<attachment123@example.com>'

        # 添加文本部分
        text_part = MIMEText('This email has an attachment.', 'plain')
        msg.attach(text_part)

        # 添加附件
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(b'PDF content here')
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
        msg.attach(attachment)

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertIn('This email has an attachment.', result['text_body'])
        self.assertEqual(len(result['attachments']), 1)

        attachment_data = result['attachments'][0]
        self.assertEqual(attachment_data['filename'], 'document.pdf')
        self.assertEqual(attachment_data['content_type'], 'application/pdf')
        self.assertIn('attachment', attachment_data['content_disposition'])
        self.assertIsNotNone(attachment_data['data'])

    def test_parse_email_with_multiple_attachments(self):
        """测试解析带多个附件的邮件"""
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Multiple Attachments'
        msg['Message-ID'] = '<multi123@example.com>'

        msg.attach(MIMEText('Email with multiple attachments.', 'plain'))

        # 添加多个附件
        for filename, content_type in [('file1.pdf', 'application/pdf'), ('file2.jpg', 'image/jpeg')]:
            attachment = MIMEBase(*content_type.split('/'))
            attachment.set_payload(b'content')
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertEqual(len(result['attachments']), 2)
        filenames = {att['filename'] for att in result['attachments']}
        self.assertIn('file1.pdf', filenames)
        self.assertIn('file2.jpg', filenames)

    def test_parse_email_with_inline_image(self):
        """测试解析带内嵌图片的邮件"""
        msg = MIMEMultipart('related')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Email with Inline Image'
        msg['Message-ID'] = '<inline123@example.com>'

        # 添加HTML部分
        html_part = MIMEText('<html><body><img src="cid:image123"></body></html>', 'html')
        msg.attach(html_part)

        # 添加内嵌图片
        image = MIMEImage(b'fake image data', 'jpeg')
        image.add_header('Content-ID', '<image123>')
        image.add_header('Content-Disposition', 'inline', filename='image.jpg')
        msg.attach(image)

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        # 内嵌图片应该被识别为附件
        self.assertEqual(len(result['attachments']), 1)
        attachment = result['attachments'][0]
        self.assertEqual(attachment['content_id'], 'image123')
        self.assertIn('inline', attachment['content_disposition'])

    def test_parse_email_without_message_id(self):
        """测试解析没有Message-ID的邮件"""
        msg = MIMEText('Test email without Message-ID.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'No Message-ID'
        # 不设置 Message-ID

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        # 应该处理空 Message-ID
        self.assertEqual(result['message_id'], '')

    def test_parse_email_without_date(self):
        """测试解析没有Date头的邮件"""
        msg = MIMEText('Test email without Date.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'No Date'
        # 不设置 Date

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        # 应该使用当前时间作为默认值
        self.assertIsInstance(result['date'], datetime)

    def test_parse_email_with_cc_and_bcc(self):
        """测试解析包含CC和BCC的邮件"""
        msg = MIMEText('Test email with CC and BCC.', 'plain')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Cc'] = 'cc@example.com'
        msg['Bcc'] = 'bcc@example.com'
        msg['Subject'] = 'CC and BCC'
        msg['Message-ID'] = '<ccbcc123@example.com>'

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        self.assertEqual(result['cc_addresses'], 'cc@example.com')
        self.assertEqual(result['bcc_addresses'], 'bcc@example.com')

    def test_parse_email_with_complex_multipart(self):
        """测试解析复杂的多部分邮件（alternative + mixed）"""
        # 创建外层 mixed 容器
        outer_msg = MIMEMultipart('mixed')
        outer_msg['From'] = 'sender@example.com'
        outer_msg['To'] = 'recipient@example.com'
        outer_msg['Subject'] = 'Complex Multipart'
        outer_msg['Message-ID'] = '<complex123@example.com>'

        # 创建内层 alternative 容器
        inner_msg = MIMEMultipart('alternative')
        inner_msg.attach(MIMEText('Plain text version.', 'plain'))
        inner_msg.attach(MIMEText('<html><body>HTML version.</body></html>', 'html'))
        outer_msg.attach(inner_msg)

        # 添加附件
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(b'PDF content')
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
        outer_msg.attach(attachment)

        email_data = outer_msg.as_bytes()
        result = MailParser.parse_email(email_data)

        # 应该提取文本和HTML
        self.assertIn('Plain text version.', result['text_body'])
        self.assertIn('HTML version.', result['html_body'])
        # 应该提取附件
        self.assertEqual(len(result['attachments']), 1)
        self.assertEqual(result['attachments'][0]['filename'], 'document.pdf')

    def test_parse_email_attachment_without_filename(self):
        """测试解析没有文件名的附件"""
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Attachment without Filename'
        msg['Message-ID'] = '<nofilename123@example.com>'

        msg.attach(MIMEText('Email body.', 'plain'))

        # 创建没有文件名的附件
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(b'binary content')
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment')
        # 不设置 filename
        msg.attach(attachment)

        email_data = msg.as_bytes()
        result = MailParser.parse_email(email_data)

        # 应该生成默认文件名
        self.assertEqual(len(result['attachments']), 1)
        self.assertIsNotNone(result['attachments'][0]['filename'])
        # 默认文件名应该包含扩展名
        self.assertTrue(result['attachments'][0]['filename'].endswith('.bin'))

    def test_get_extension_from_content_type(self):
        """测试从内容类型获取文件扩展名"""
        self.assertEqual(MailParser._get_extension_from_content_type('text/plain'), '.txt')
        self.assertEqual(MailParser._get_extension_from_content_type('text/html'), '.html')
        self.assertEqual(MailParser._get_extension_from_content_type('image/jpeg'), '.jpg')
        self.assertEqual(MailParser._get_extension_from_content_type('image/png'), '.png')
        self.assertEqual(MailParser._get_extension_from_content_type('application/pdf'), '.pdf')
        self.assertEqual(MailParser._get_extension_from_content_type('application/zip'), '.zip')
        self.assertEqual(MailParser._get_extension_from_content_type('application/json'), '.json')
        # 未知类型应该返回 .bin
        self.assertEqual(MailParser._get_extension_from_content_type('unknown/type'), '.bin')
