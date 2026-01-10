"""
单元测试：OSSIntegrationService OSS 集成服务

测试覆盖：
- upload_attachment (上传附件)
- download_attachment (下载附件)
- delete_attachment (删除附件)
- get_attachment_metadata (获取附件元数据)
"""
from unittest import TestCase

from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock

from app_mailserver.services.oss_integration_service import OSSIntegrationService


class TestOSSIntegrationService(TestCase):
    """测试 OSSIntegrationService"""

    databases = {'default', 'mailserver_rw'}

    def setUp(self):
        """每个测试前设置"""
        # 清除单例实例，确保每个测试都从干净状态开始
        from common.components.singleton import _Singleton
        if hasattr(_Singleton, '_instances') and OSSIntegrationService in _Singleton._instances:
            del _Singleton._instances[OSSIntegrationService]

        # Mock 配置
        self.mock_config = {
            'oss_bucket': 'test-bucket',
            'oss_endpoint': 'http://localhost:8000/api/oss'
        }

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_init_success(self, mock_boto3, mock_get_config):
        """测试成功初始化 OSS 服务"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        self.assertEqual(service.bucket, 'test-bucket')
        self.assertIsNotNone(service.s3_client)
        mock_boto3.client.assert_called_once()

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_upload_attachment_success(self, mock_boto3, mock_get_config):
        """测试成功上传附件"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        result = service.upload_attachment(
            key='test/file.pdf',
            data=b'PDF content',
            content_type='application/pdf',
            metadata={'message_id': '123'}
        )

        self.assertEqual(result['bucket'], 'test-bucket')
        self.assertEqual(result['key'], 'test/file.pdf')
        self.assertEqual(result['size'], len(b'PDF content'))

        # 验证调用了 S3 client
        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args[1]
        self.assertEqual(call_kwargs['Bucket'], 'test-bucket')
        self.assertEqual(call_kwargs['Key'], 'test/file.pdf')
        self.assertEqual(call_kwargs['Body'], b'PDF content')
        self.assertEqual(call_kwargs['ContentType'], 'application/pdf')
        self.assertIn('Metadata', call_kwargs)

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_upload_attachment_without_content_type(self, mock_boto3, mock_get_config):
        """测试上传附件时不指定内容类型"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        result = service.upload_attachment(
            key='test/file.bin',
            data=b'Binary content'
        )

        self.assertEqual(result['bucket'], 'test-bucket')

        # 验证 ContentType 不在调用参数中
        call_kwargs = mock_s3_client.put_object.call_args[1]
        self.assertNotIn('ContentType', call_kwargs)

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_upload_attachment_error(self, mock_boto3, mock_get_config):
        """测试上传附件时发生错误"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_s3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'PutObject'
        )
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        with self.assertRaises(ClientError):
            service.upload_attachment(
                key='test/file.pdf',
                data=b'PDF content'
            )

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_download_attachment_success(self, mock_boto3, mock_get_config):
        """测试成功下载附件"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_response = {
            'Body': MagicMock(read=MagicMock(return_value=b'attachment data'))
        }
        mock_s3_client.get_object.return_value = mock_response
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        data = service.download_attachment('test/file.pdf')

        self.assertEqual(data, b'attachment data')

        # 验证调用了 S3 client
        mock_s3_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.pdf'
        )

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_download_attachment_not_found(self, mock_boto3, mock_get_config):
        """测试下载不存在的附件"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}},
            'GetObject'
        )
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        with self.assertRaises(ClientError):
            service.download_attachment('test/nonexistent.pdf')

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_delete_attachment_success(self, mock_boto3, mock_get_config):
        """测试成功删除附件"""
        # 设置 mock
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        # 明确设置 delete_object 的返回值，模拟 S3 delete_object 的正常返回
        # 注意：S3 delete_object 成功时通常返回空字典或包含 DeleteMarker 的字典，不会抛出异常
        mock_s3_client.delete_object.return_value = {'DeleteMarker': True}
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        result = service.delete_attachment('test/file.pdf')

        self.assertTrue(result)

        # 验证调用了 S3 client
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.pdf'
        )

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_delete_attachment_error(self, mock_boto3, mock_get_config):
        """测试删除附件时发生错误"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'DeleteObject'
        )
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        result = service.delete_attachment('test/file.pdf')

        # 应该返回 False，不抛出异常
        self.assertFalse(result)

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_get_attachment_metadata_success(self, mock_boto3, mock_get_config):
        """测试成功获取附件元数据"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        from datetime import datetime
        mock_response = {
            'ContentType': 'application/pdf',
            'ContentLength': 1024,
            'LastModified': datetime.now(),
            'ETag': '"abc123"',
            'Metadata': {'message_id': '123', 'filename': 'test.pdf'}
        }
        mock_s3_client.head_object.return_value = mock_response
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        metadata = service.get_attachment_metadata('test/file.pdf')

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['ContentType'], 'application/pdf')
        self.assertEqual(metadata['ContentLength'], 1024)
        self.assertEqual(metadata['ETag'], 'abc123')  # 应该去掉引号
        self.assertIn('Metadata', metadata)

        # 验证调用了 S3 client
        mock_s3_client.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.pdf'
        )

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_get_attachment_metadata_not_found(self, mock_boto3, mock_get_config):
        """测试获取不存在附件的元数据"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadObject'
        )
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        metadata = service.get_attachment_metadata('test/nonexistent.pdf')

        # 应该返回 None，不抛出异常
        self.assertIsNone(metadata)

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_get_attachment_metadata_default_values(self, mock_boto3, mock_get_config):
        """测试获取附件元数据时使用默认值"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        # 返回缺少某些字段的响应
        mock_response = {}
        mock_s3_client.head_object.return_value = mock_response
        mock_boto3.client.return_value = mock_s3_client

        service = OSSIntegrationService()

        metadata = service.get_attachment_metadata('test/file.pdf')

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['ContentType'], 'application/octet-stream')  # 默认值
        self.assertEqual(metadata['ContentLength'], 0)  # 默认值
        self.assertEqual(metadata['ETag'], '')  # 默认值
        self.assertEqual(metadata['Metadata'], {})  # 默认值

    @patch('app_mailserver.services.oss_integration_service.get_app_config')
    @patch('app_mailserver.services.oss_integration_service.boto3')
    def test_get_oss_service_singleton(self, mock_boto3, mock_get_config):
        """测试 OSS 服务的单例模式"""
        mock_get_config.return_value = self.mock_config
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        # 清除之前的单例实例（如果存在）
        from common.components.singleton import _Singleton
        # 清除 OSSIntegrationService 的所有单例实例
        if hasattr(_Singleton, '_instances') and OSSIntegrationService in _Singleton._instances:
            del _Singleton._instances[OSSIntegrationService]

        service1 = OSSIntegrationService()
        service2 = OSSIntegrationService()

        # 应该是同一个实例
        self.assertIs(service1, service2)
