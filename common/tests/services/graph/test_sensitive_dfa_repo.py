import unittest
from unittest import TestCase


@unittest.skip(
    "SensitiveDfaFilter lived in app_txt; common tests must not import app_* — "
    "add a common-side implementation or move this test to the owning app."
)
class TestSensitiveDfaRepo(TestCase):
    def test_get_sensitive_words(self):
        pass
