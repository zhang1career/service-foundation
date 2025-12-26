import logging

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from common.components.singleton import Singleton
from common.consts.http_const import CONTENT_TYPE_MAP
from common.consts.s3_const import CLIENT_METHOD_GET

logger = logging.getLogger(__name__)


class S3Client(Singleton):
    s3_client = boto3.client("s3",
                             aws_access_key_id=settings.AWS_ACCESS_ID,
                             aws_secret_access_key=settings.AWS_ACCESS_KEY)

    def get_client(self):
        return self.s3_client


def upload(file_path, content_type, obj_name):
    """
    Upload a file to s3.

    @param file_path: Where the file is.
    @param content_type: The file type, e.g. CONTENT_TYPE_JPG, CONTENT_TYPE_MP3.
    @param obj_name: The name of the object to be stored.
    @return: The URL of the file uploaded.
    """
    logger.info("[s3_upload] param file_path=%s, obj_name=%s", file_path, obj_name)

    s3_client = S3Client().get_client()
    with open(file_path, "rb") as f:
        s3_client.upload_fileobj(f, settings.S3_BUCKET_DATA_ANALYZE, obj_name,
                                 ExtraArgs=_build_ext_args(content_type))
    ret = _generate_presigned_url(s3_client, obj_name, CLIENT_METHOD_GET)
    return ret


def download(obj_name, new_name):
    logger.info("[s3_download] param obj_name=%s, new_name=%s", obj_name, new_name)

    s3_client = S3Client().get_client()
    s3_client.download_file(settings.S3_BUCKET_DATA_ANALYZE, obj_name, new_name)


def download_obj(obj_name, new_name):
    logger.info("[s3_download_obj] param obj_name=%s, new_name=%s", obj_name, new_name)

    s3_client = S3Client().get_client()
    s3_client.download_fileobj(settings.S3_BUCKET_DATA_ANALYZE, obj_name, new_name)


def _generate_presigned_url(s3_client, obj_name, client_method, expires_in=604800):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action.

    :param s3_client: A Boto3 Amazon S3 client.
    :param obj_name: The name of the object to be stored
    :param client_method: The method of the client requests
    :param expires_in: The lifetime of the url to be generated
    :return: The presigned URL.
    """
    logger.info("[s3_url] param s3_client=%s, obj_name=%s, client_method=%s, expires_in=%d", s3_client, obj_name,
                client_method, expires_in)
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": settings.S3_BUCKET_DATA_ANALYZE, "Key": obj_name},
            ExpiresIn=expires_in
        )
    except ClientError:
        logger.exception("[s3_url] generating url failed, obj_name=%s, client_method=%s", obj_name, client_method)
        raise
    logger.info("[s3_url] result url=%s", url)
    return url


def _build_ext_args(content_type):
    return {
        "ContentType": CONTENT_TYPE_MAP[content_type],
        "ACL": "public-read"
    }
