"""
单元测试：S3兼容视图，包括文件复制功能

测试覆盖：
- 文件上传
- 文件复制（同一bucket内）
- 文件复制（跨bucket）
- 复制时的元数据处理
- 错误处理
"""
import tempfile
import shutil

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from app_oss.views.s3_compatible_view import S3PutObjectView
from app_oss.services.oss_client import OSSClient


class TestS3PutObjectView(TestCase):
    """测试S3PutObjectView，包括上传和复制功能"""

    def setUp(self):
        """每个测试前设置临时存储目录"""
        import os
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
        # 设置环境变量
        self.original_storage_path = os.environ.get('OSS_STORAGE_PATH')
        self.original_bucket_name = os.environ.get('OSS_BUCKET_NAME')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        os.environ['OSS_BUCKET_NAME'] = 'test-bucket'
        
        # 清除OSSClient单例实例，以便重新初始化
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        
        # 创建测试用的bucket和文件
        self.bucket1 = 'test-bucket-1'
        self.bucket2 = 'test-bucket-2'
        self.source_key = 'source/file.txt'
        self.dest_key = 'dest/file.txt'
        self.test_content = b'This is test content for file copy'
        
        # 初始化OSS客户端并上传源文件
        client = OSSClient()
        local_storage = client.get_local_storage()
        local_storage.put_object(
            bucket_name=self.bucket1,
            object_key=self.source_key,
            data=self.test_content,
            content_type='text/plain',
            metadata={'original': 'true'}
        )
        
        self.factory = APIRequestFactory()
        self.view = S3PutObjectView.as_view()

    def tearDown(self):
        """每个测试后清理临时目录"""
        import os
        # 恢复原始环境变量
        if self.original_storage_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self.original_storage_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
            
        if self.original_bucket_name is not None:
            os.environ['OSS_BUCKET_NAME'] = self.original_bucket_name
        elif 'OSS_BUCKET_NAME' in os.environ:
            del os.environ['OSS_BUCKET_NAME']
        
        # 清除OSSClient单例实例
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_regular_upload(self):
        """测试正常上传功能（确保复制功能不影响原有功能）"""
        request = self.factory.put(
            f'/{self.bucket1}/uploaded.txt',
            data=b'Uploaded content',
            content_type='text/plain'
        )
        request.META['CONTENT_TYPE'] = 'text/plain'
        
        response = self.view(request, bucket=self.bucket1, key='uploaded.txt')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('ETag', response)
        
        # 验证文件已上传
        client = OSSClient()
        local_storage = client.get_local_storage()
        result = local_storage.get_object(
            bucket_name=self.bucket1,
            object_key='uploaded.txt'
        )
        self.assertEqual(result['Body'], b'Uploaded content')

    def test_copy_within_same_bucket(self):
        """测试同一bucket内复制文件"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        
        # 验证响应包含ETag和LastModified
        self.assertIn(b'<ETag>', response.content)
        self.assertIn(b'<LastModified>', response.content)
        
        # 验证目标文件已创建且内容正确
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.get_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        self.assertEqual(dest_result['Body'], self.test_content)
        
        # 验证源文件仍然存在
        source_result = local_storage.get_object(
            bucket_name=self.bucket1,
            object_key=self.source_key
        )
        self.assertEqual(source_result['Body'], self.test_content)

    def test_copy_between_buckets(self):
        """测试跨bucket复制文件"""
        request = self.factory.put(f'/{self.bucket2}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        
        response = self.view(request, bucket=self.bucket2, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证目标bucket中的文件已创建
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.get_object(
            bucket_name=self.bucket2,
            object_key=self.dest_key
        )
        self.assertEqual(dest_result['Body'], self.test_content)

    def test_copy_with_metadata_copy_directive(self):
        """测试复制时保留源文件的元数据（COPY指令）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        request.META['HTTP_X_AMZ_METADATA_DIRECTIVE'] = 'COPY'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证元数据被保留
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.head_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        self.assertEqual(dest_result.get('Metadata', {}).get('original'), 'true')

    def test_copy_with_metadata_replace_directive(self):
        """测试复制时替换元数据（REPLACE指令）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        request.META['HTTP_X_AMZ_METADATA_DIRECTIVE'] = 'REPLACE'
        request.META['HTTP_X_AMZ_META_NEW_KEY'] = 'new_value'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证新元数据被设置
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.head_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        metadata = dest_result.get('Metadata', {})
        self.assertEqual(metadata.get('new-key'), 'new_value')
        # 源文件的元数据不应该被保留（REPLACE模式）
        self.assertNotIn('original', metadata)

    def test_copy_with_additional_metadata(self):
        """测试复制时添加额外的元数据"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        request.META['HTTP_X_AMZ_METADATA_DIRECTIVE'] = 'COPY'
        request.META['HTTP_X_AMZ_META_ADDITIONAL'] = 'additional_value'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证元数据被合并
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.head_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        metadata = dest_result.get('Metadata', {})
        self.assertEqual(metadata.get('original'), 'true')
        self.assertEqual(metadata.get('additional'), 'additional_value')

    def test_copy_nonexistent_source(self):
        """测试复制不存在的源文件"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/nonexistent.txt'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Source object not found', response.content)

    def test_copy_with_url_encoded_source(self):
        """测试URL编码的copy-source"""
        # 创建一个带特殊字符的文件名
        special_key = 'source/file with spaces.txt'
        client = OSSClient()
        local_storage = client.get_local_storage()
        local_storage.put_object(
            bucket_name=self.bucket1,
            object_key=special_key,
            data=self.test_content,
            content_type='text/plain'
        )
        
        # URL编码的路径
        from urllib.parse import quote
        encoded_source = f'/{self.bucket1}/{quote(special_key)}'
        
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = encoded_source
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证文件已复制
        dest_result = local_storage.get_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        self.assertEqual(dest_result['Body'], self.test_content)

    def test_copy_with_invalid_source_format_missing_slash(self):
        """测试无效的copy-source格式（缺少斜杠）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = 'invalid-format'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid x-amz-copy-source format', response.content)

    def test_copy_with_invalid_source_format_missing_key(self):
        """测试无效的copy-source格式（缺少key）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid x-amz-copy-source: missing key', response.content)

    def test_copy_with_copy_source_without_leading_slash(self):
        """测试copy-source不带前导斜杠（应该也能正常工作）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'{self.bucket1}/{self.source_key}'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证文件已复制
        client = OSSClient()
        local_storage = client.get_local_storage()
        dest_result = local_storage.get_object(
            bucket_name=self.bucket1,
            object_key=self.dest_key
        )
        self.assertEqual(dest_result['Body'], self.test_content)

    def test_copy_response_format(self):
        """测试复制操作的响应格式（XML格式）"""
        request = self.factory.put(f'/{self.bucket1}/{self.dest_key}')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/{self.source_key}'
        
        response = self.view(request, bucket=self.bucket1, key=self.dest_key)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        
        # 验证XML结构
        content = response.content.decode('utf-8')
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', content)
        self.assertIn('<CopyObjectResult', content)
        self.assertIn('<ETag>', content)
        self.assertIn('<LastModified>', content)

    def test_copy_preserves_content_type(self):
        """测试复制时保留内容类型"""
        # 创建一个有特定content-type的文件
        client = OSSClient()
        local_storage = client.get_local_storage()
        local_storage.put_object(
            bucket_name=self.bucket1,
            object_key='source/image.jpg',
            data=b'fake image data',
            content_type='image/jpeg',
            metadata={}
        )
        
        request = self.factory.put(f'/{self.bucket1}/dest/image.jpg')
        request.META['HTTP_X_AMZ_COPY_SOURCE'] = f'/{self.bucket1}/source/image.jpg'
        
        response = self.view(request, bucket=self.bucket1, key='dest/image.jpg')
        
        self.assertEqual(response.status_code, 200)
        
        # 验证内容类型被保留
        dest_result = local_storage.head_object(
            bucket_name=self.bucket1,
            object_key='dest/image.jpg'
        )
        self.assertEqual(dest_result.get('ContentType'), 'image/jpeg')

