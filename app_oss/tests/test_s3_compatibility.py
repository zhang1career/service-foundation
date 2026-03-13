"""
S3 compatibility tests: error responses, Range, ListObjects V1/V2, ListBuckets, DeleteMultipleObjects
"""
import os
import tempfile
import shutil

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from app_oss.services.oss_client import OSSClient
from app_oss.views.s3_compatible_view import (
    S3GetObjectView,
    S3HeadObjectView,
    S3ListObjectsView,
)
from app_oss.views.s3_bucket_view import S3ListBucketsView, S3DeleteMultipleObjectsView


class TestS3ErrorResponse(TestCase):
    """Test S3 XML error format for boto3 compatibility"""

    databases = {'default', 'oss_rw'}

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_path = os.environ.get('OSS_STORAGE_PATH')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        self.factory = APIRequestFactory()

    def tearDown(self):
        if self._orig_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self._orig_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_object_404_returns_nosuchkey_xml(self):
        view = S3GetObjectView.as_view()
        request = self.factory.get('/bucket/nonexistent')
        response = view(request, bucket='bucket', key='nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertIn(b'<Code>NoSuchKey</Code>', response.content)

    def test_head_object_404_returns_nosuchkey_xml(self):
        view = S3HeadObjectView.as_view()
        request = self.factory.head('/bucket/nonexistent')
        response = view(request, bucket='bucket', key='nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'<Code>NoSuchKey</Code>', response.content)


class TestRangeRequest(TestCase):
    """Test GetObject Range header support"""

    databases = {'default', 'oss_rw'}

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_path = os.environ.get('OSS_STORAGE_PATH')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        client = OSSClient()
        local = client.get_local_storage()
        local.put_object('b', 'f', data=b'0123456789' * 20, content_type='text/plain')
        self.factory = APIRequestFactory()

    def tearDown(self):
        if self._orig_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self._orig_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_range_bytes_returns_206(self):
        view = S3GetObjectView.as_view()
        request = self.factory.get('/b/f')
        request.META['HTTP_RANGE'] = 'bytes=0-99'
        response = view(request, bucket='b', key='f')
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Range'], 'bytes 0-99/200')
        self.assertEqual(len(response.content), 100)
        self.assertEqual(response.content, b'0' * 10 + b'123456789' * 10)

    def test_invalid_range_returns_416(self):
        view = S3GetObjectView.as_view()
        request = self.factory.get('/b/f')
        request.META['HTTP_RANGE'] = 'bytes=300-400'
        response = view(request, bucket='b', key='f')
        self.assertEqual(response.status_code, 416)
        self.assertIn(b'<Code>InvalidRange</Code>', response.content)


class TestListObjectsV1AndDelimiter(TestCase):
    """Test ListObjects V1 and delimiter"""

    databases = {'default', 'oss_rw'}

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_path = os.environ.get('OSS_STORAGE_PATH')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        client = OSSClient()
        local = client.get_local_storage()
        for k in ['a/1', 'a/2', 'b/1', 'c']:
            local.put_object('bucket', k, data=b'x', content_type='text/plain')
        self.factory = APIRequestFactory()

    def tearDown(self):
        if self._orig_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self._orig_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_objects_v1(self):
        view = S3ListObjectsView.as_view()
        request = self.factory.get('/bucket', {'list-type': '1'})
        response = view(request, bucket='bucket')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<ListBucketResult', content)
        self.assertIn('<Contents>', content)

    def test_list_objects_delimiter(self):
        view = S3ListObjectsView.as_view()
        request = self.factory.get('/bucket', {'list-type': '2', 'delimiter': '/'})
        response = view(request, bucket='bucket')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<CommonPrefixes>', content)
        self.assertIn('<Prefix>a/</Prefix>', content)
        self.assertIn('<Prefix>b/</Prefix>', content)
        self.assertIn('<Key>c</Key>', content)


class TestListBuckets(TestCase):
    """Test ListBuckets GET /"""

    databases = {'default', 'oss_rw'}

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_path = os.environ.get('OSS_STORAGE_PATH')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        client = OSSClient()
        local = client.get_local_storage()
        local.put_object('bucket1', 'x', data=b'1', content_type='text/plain')
        local.put_object('bucket2', 'y', data=b'2', content_type='text/plain')
        self.factory = APIRequestFactory()

    def tearDown(self):
        if self._orig_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self._orig_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_buckets(self):
        view = S3ListBucketsView.as_view()
        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<ListAllMyBucketsResult>', content)
        self.assertIn('<Name>bucket1</Name>', content)
        self.assertIn('<Name>bucket2</Name>', content)


class TestDeleteMultipleObjects(TestCase):
    """Test POST ?delete batch delete"""

    databases = {'default', 'oss_rw'}

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_path = os.environ.get('OSS_STORAGE_PATH')
        os.environ['OSS_STORAGE_PATH'] = self.temp_dir
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        client = OSSClient()
        local = client.get_local_storage()
        local.put_object('b', 'k1', data=b'1', content_type='text/plain')
        local.put_object('b', 'k2', data=b'2', content_type='text/plain')
        self.factory = APIRequestFactory()

    def tearDown(self):
        if self._orig_path is not None:
            os.environ['OSS_STORAGE_PATH'] = self._orig_path
        elif 'OSS_STORAGE_PATH' in os.environ:
            del os.environ['OSS_STORAGE_PATH']
        if hasattr(OSSClient, '_instance'):
            delattr(OSSClient, '_instance')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_delete_multiple_objects(self):
        view = S3DeleteMultipleObjectsView.as_view()
        body = '''<?xml version="1.0" encoding="UTF-8"?>
<Delete xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Object><Key>k1</Key></Object>
  <Object><Key>k2</Key></Object>
</Delete>'''
        request = self.factory.post('/b?delete', body, content_type='application/xml')
        response = view(request, bucket='b')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<Deleted><Key>k1</Key></Deleted>', content)
        self.assertIn('<Deleted><Key>k2</Key></Deleted>', content)
        # Objects should be gone
        local = OSSClient().get_local_storage()
        self.assertFalse(local.object_exists('b', 'k1'))
        self.assertFalse(local.object_exists('b', 'k2'))
