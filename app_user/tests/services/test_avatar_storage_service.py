import io
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from app_user.services import avatar_storage_service as av
from common.exceptions import InvalidArgumentError, ObjectStorageError
from common.services.http import HttpCallError

# Minimal valid 1×1 PNG (bytes)
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestUploadAvatarNoneAndEmpty(SimpleTestCase):
    def test_none_returns_empty_string(self):
        self.assertEqual(av.upload_avatar(None), "")

    def test_empty_string_returns_empty(self):
        self.assertEqual(av.upload_avatar("   "), "")


class TestUploadAvatarUnsupported(SimpleTestCase):
    def test_non_file_non_str_raises(self):
        with self.assertRaises(InvalidArgumentError) as ctx:
            av.upload_avatar(12345)
        self.assertIn("unsupported", str(ctx.exception).lower())


class TestUploadAvatarBase64(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_raw_base64_uploads(self, _b, _u, mock_put):
        import base64

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        b64 = base64.b64encode(_TINY_PNG).decode("ascii")
        url = av.upload_avatar(b64)
        self.assertTrue(url.startswith("/api/oss/bucket1/"))
        mock_put.assert_called_once()
        self.assertEqual(mock_put.call_args.kwargs["data"], _TINY_PNG)

    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_invalid_base64_raises(self, _b, _u, mock_put):
        with self.assertRaises(InvalidArgumentError) as ctx:
            av.upload_avatar("not-valid-base64!!!")
        self.assertIn("avatar", str(ctx.exception).lower())
        mock_put.assert_not_called()


class TestUploadAvatarDataUrl(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_data_url_png(self, _b, _u, mock_put):
        import base64

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        enc = base64.b64encode(_TINY_PNG).decode("ascii")
        data_url = f"data:image/png;base64,{enc}"
        av.upload_avatar(data_url)
        mock_put.assert_called_once()
        self.assertEqual(mock_put.call_args.kwargs["content_type"], "image/png")

    def test_malformed_data_url_raises(self):
        with self.assertRaises(InvalidArgumentError):
            av.upload_avatar("data:image/png;base64,@@@@")


class TestUploadAvatarFileLike(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_file_object_upload(self, _b, _u, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        buf = io.BytesIO(_TINY_PNG)
        f = MagicMock()
        f.read = buf.read
        f.content_type = "image/png"
        f.name = "shot.png"
        buf.seek(0)
        av.upload_avatar(f)
        mock_put.assert_called_once()
        self.assertGreater(mock_put.call_args.kwargs["timeout"], 0)

    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_empty_file_raises(self, _b, _u, mock_put):
        f = MagicMock()
        f.read = lambda: b""
        f.content_type = "image/png"
        f.name = "empty.png"
        with self.assertRaises(InvalidArgumentError) as ctx:
            av.upload_avatar(f)
        self.assertIn("empty", str(ctx.exception).lower())


class TestUploadAvatarHttpErrors(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_put_non_200_raises_object_storage(self, _b, _u, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "denied"
        mock_put.return_value = mock_resp
        import base64

        with self.assertRaises(ObjectStorageError) as ctx:
            av.upload_avatar(base64.b64encode(_TINY_PNG).decode("ascii"))
        self.assertIn("403", str(ctx.exception))

    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_put_http_call_error_raises(self, _b, _u, mock_put):
        mock_put.side_effect = HttpCallError("timeout")
        import base64

        with self.assertRaises(ObjectStorageError):
            av.upload_avatar(base64.b64encode(_TINY_PNG).decode("ascii"))


class TestUploadAvatarRemoteUrl(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_download_remote")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_http_url_uses_download_then_put(self, _b, _u, mock_dl, mock_put):
        mock_dl.return_value = (_TINY_PNG, "image/png", "x.png")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        av.upload_avatar("https://cdn.example.com/a.png")
        mock_dl.assert_called_once()
        mock_put.assert_called_once()

    @patch.object(av, "_download_remote")
    @patch.object(av, "_oss_base_url", return_value="http://oss.test")
    @patch.object(av, "_oss_bucket_name", return_value="bucket1")
    def test_download_non_200_raises_invalid_argument(self, _b, _u, mock_dl):
        mock_dl.side_effect = InvalidArgumentError("failed to fetch avatar url")
        with self.assertRaises(InvalidArgumentError):
            av.upload_avatar("https://cdn.example.com/missing.png")


@override_settings(USER_OSS_ENDPOINT="https://custom-oss.example/api")
class TestOssSettings(SimpleTestCase):
    @patch.object(av, "_http_put_object")
    @patch.object(av, "_oss_bucket_name", return_value="b")
    def test_custom_endpoint_used_in_upload_url(self, _bn, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        import base64

        av.upload_avatar(base64.b64encode(_TINY_PNG).decode("ascii"))
        upload_url = mock_put.call_args.kwargs["url"]
        self.assertTrue(upload_url.startswith("https://custom-oss.example/api/b/"))
