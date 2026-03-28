from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from common.services.storage.s3_service import _build_ext_args, _generate_presigned_url, upload


class S3ServiceTest(TestCase):
    @patch("common.services.storage.s3_service.settings")
    def test_generate_presigned_url(self, settings_mock):
        settings_mock.S3_BUCKET_DATA_ANALYZE = "bucket-a"
        s3_client = MagicMock()
        s3_client.generate_presigned_url.return_value = "https://signed-url"

        url = _generate_presigned_url(s3_client, "obj.txt", "get_object", expires_in=60)
        self.assertEqual(url, "https://signed-url")
        s3_client.generate_presigned_url.assert_called_once()

    @patch("common.services.storage.s3_service._generate_presigned_url")
    @patch("common.services.storage.s3_service.get_s3_client")
    @patch("builtins.open", new_callable=mock_open, read_data=b"abc")
    @patch("common.services.storage.s3_service.settings")
    def test_upload_success(self, settings_mock, open_mock, get_client_mock, signed_url_mock):
        settings_mock.S3_BUCKET_DATA_ANALYZE = "bucket-a"
        client = MagicMock()
        get_client_mock.return_value = client
        signed_url_mock.return_value = "https://signed-url"

        url = upload("/tmp/file.txt", "png", "file.txt")
        self.assertEqual(url, "https://signed-url")
        open_mock.assert_called_once_with("/tmp/file.txt", "rb")
        client.upload_fileobj.assert_called_once()

    def test_build_ext_args(self):
        ret = _build_ext_args("png")
        self.assertIn("ContentType", ret)
        self.assertEqual(ret["ACL"], "public-read")
