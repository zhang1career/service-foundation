from unittest import TestCase


class TestSensitiveDfaRepo(TestCase):
    def setUp(self):
        from app_txt.repos.sensitive_filter_repo import SensitiveDfaFilter
        self.dut = SensitiveDfaFilter()


    def test_get_sensitive_words(self):
        # 测试获取敏感词
        words = self.dut.get_sensitive_words()
        self.assertIsInstance(words, list)
        print(words)
