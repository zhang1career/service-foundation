"""
S3-compatible XML error response

Provides S3 standard error format for boto3 and other S3 clients to parse.
Reference: ref/minio/cmd/api-errors.go, AWS S3 REST API error response format.
"""
import uuid
from django.http import HttpResponse


# S3 error codes and their HTTP status codes
ERROR_CODES = {
    'NoSuchKey': 404,
    'NoSuchBucket': 404,
    'InvalidRequest': 400,
    'InvalidArgument': 400,
    'InvalidRange': 416,
    'MethodNotAllowed': 405,
    'MalformedXML': 400,
    'InternalError': 500,
}


def s3_error_response(
    code: str,
    message: str = None,
    resource: str = '',
    request_id: str = None,
) -> HttpResponse:
    """
    Build S3-compatible XML error response.

    Args:
        code: S3 error code (e.g., NoSuchKey, InternalError)
        message: Human-readable error description
        resource: Requested resource path
        request_id: Optional request ID for tracing

    Returns:
        HttpResponse with Content-Type application/xml
    """
    status = ERROR_CODES.get(code, 500)
    if message is None:
        message = _default_message(code)
    if request_id is None:
        request_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

    xml_body = _build_error_xml(code=code, message=message, resource=resource, request_id=request_id)
    response = HttpResponse(xml_body, content_type='application/xml', status=status)
    return response


def _default_message(code: str) -> str:
    defaults = {
        'NoSuchKey': 'The specified key does not exist.',
        'NoSuchBucket': 'The specified bucket does not exist.',
        'InvalidRequest': 'Invalid request.',
        'InvalidArgument': 'Invalid argument.',
        'InvalidRange': 'The requested range cannot be satisfied.',
        'MethodNotAllowed': 'The specified method is not allowed against this resource.',
    'MalformedXML': 'The XML you provided was not well-formed.',
    'InternalError': 'We encountered an internal error. Please try again.',
}
    return defaults.get(code, str(code))


def _build_error_xml(code: str, message: str, resource: str, request_id: str) -> bytes:
    """Build S3 Error XML body, properly escaped."""
    from xml.sax.saxutils import escape
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Error xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n'
        f'  <Code>{escape(code)}</Code>\n'
        f'  <Message>{escape(message)}</Message>\n'
        f'  <Resource>{escape(resource)}</Resource>\n'
        f'  <RequestId>{escape(request_id)}</RequestId>\n'
        '</Error>'
    ).encode('utf-8')
