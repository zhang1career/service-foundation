"""
S3 bucket-level operations: ListBuckets, DeleteMultipleObjects
"""
import logging
import xml.etree.ElementTree as ET
from django.http import HttpResponse
from rest_framework.views import APIView
from xml.sax.saxutils import escape

from app_oss.services.oss_client import OSSClient
from app_oss.utils.s3_error_response import s3_error_response

logger = logging.getLogger(__name__)


class S3ListBucketsView(APIView):
    """GET / - List all buckets"""

    def get(self, request):
        try:
            client = OSSClient()
            local_storage = client.get_local_storage()
            buckets = local_storage.list_buckets()

            from datetime import datetime
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

            xml_parts = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
                '<Owner><ID>unknown</ID><DisplayName>unknown</DisplayName></Owner>',
                '<Buckets>',
            ]
            for name in sorted(buckets):
                xml_parts.append(f'  <Bucket><Name>{escape(name)}</Name><CreationDate>{now}</CreationDate></Bucket>')
            xml_parts.append('</Buckets>')
            xml_parts.append('</ListAllMyBucketsResult>')

            return HttpResponse('\n'.join(xml_parts), content_type='application/xml')
        except Exception as e:
            logger.exception(f"[ListBuckets] Error: {e}")
            return s3_error_response('InternalError', str(e), resource='/')

    def head(self, request):
        return HttpResponse(status=200)


class S3DeleteMultipleObjectsView(APIView):
    """POST /{bucket}?delete - Delete multiple objects"""

    def post(self, request, bucket: str):
        resource = f'/{bucket}'
        try:
            body = request.body
            if not body:
                return s3_error_response('InvalidRequest', 'Request body is required', resource=resource)

            root = ET.fromstring(body)
            # Support both with and without S3 namespace
            ns = 'http://s3.amazonaws.com/doc/2006-03-01/'
            keys = []
            for obj in root.findall(f'.//{{{ns}}}Object') or root.findall('.//Object'):
                key_el = obj.find(f'{{{ns}}}Key') or obj.find('Key')
                if key_el is not None and key_el.text:
                    keys.append(key_el.text.strip())

            if not keys:
                return s3_error_response('InvalidRequest', 'No objects specified', resource=resource)

            client = OSSClient()
            local_storage = client.get_local_storage()
            result = local_storage.delete_objects(bucket_name=bucket, keys=keys)

            # Build DeleteResult XML
            xml_parts = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<DeleteResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
            ]
            for d in result.get('Deleted', []):
                xml_parts.append(f'  <Deleted><Key>{escape(d["Key"])}</Key></Deleted>')
            for err in result.get('Errors', []):
                xml_parts.append(
                    f'  <Error><Key>{escape(err["Key"])}</Key>'
                    f'<Code>{escape(err.get("Code", "InternalError"))}</Code>'
                    f'<Message>{escape(err.get("Message", ""))}</Message></Error>'
                )
            xml_parts.append('</DeleteResult>')

            return HttpResponse('\n'.join(xml_parts), content_type='application/xml')
        except ET.ParseError as e:
            return s3_error_response('MalformedXML', str(e), resource=resource)
        except Exception as e:
            logger.exception(f"[DeleteMultipleObjects] Error: {e}")
            return s3_error_response('InternalError', str(e), resource=resource)
