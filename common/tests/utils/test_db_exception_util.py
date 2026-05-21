from django.db import IntegrityError
from django.test import SimpleTestCase

from common.consts.response_const import RET_DB_DUPLICATE_KEY, RET_RESOURCE_EXISTS
from common.utils.db_exception_util import integrity_error_to_client, normalize_optional_contact


class DbExceptionUtilTest(SimpleTestCase):
    def test_normalize_optional_contact(self):
        self.assertIsNone(normalize_optional_contact(None))
        self.assertIsNone(normalize_optional_contact(""))
        self.assertIsNone(normalize_optional_contact("  "))
        self.assertEqual(normalize_optional_contact(" a@b.c "), "a@b.c")

    def test_integrity_error_email(self):
        exc = IntegrityError("Duplicate entry '' for key 'user.email'")
        code, msg = integrity_error_to_client(exc)
        self.assertEqual(code, RET_RESOURCE_EXISTS)
        self.assertEqual(msg, "email already exists")

    def test_integrity_error_phone(self):
        exc = IntegrityError("Duplicate entry for key 'user.phone'")
        code, msg = integrity_error_to_client(exc)
        self.assertEqual(code, RET_RESOURCE_EXISTS)
        self.assertEqual(msg, "phone already exists")

    def test_integrity_error_username(self):
        exc = IntegrityError("Duplicate entry for key 'user.name'")
        code, msg = integrity_error_to_client(exc)
        self.assertEqual(code, RET_RESOURCE_EXISTS)
        self.assertEqual(msg, "username already exists")

    def test_integrity_error_generic(self):
        exc = IntegrityError("some other constraint")
        code, msg = integrity_error_to_client(exc)
        self.assertEqual(code, RET_DB_DUPLICATE_KEY)
        self.assertEqual(msg, "数据冲突")
