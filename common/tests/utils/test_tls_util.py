from unittest import TestCase

from common.utils.tls_util import check_version


class TestTlsUtil(TestCase):

    def test_check_package(self):
        result = check_version()
        print(result)
