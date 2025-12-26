from unittest import TestCase

from common.utils.url_util import remove_url_param, extract_sub_url, url_encode, url_decode, extract_domain


class Test(TestCase):
    def test_remove_url_param(self):
        _input = "https://example.com/path/to/resource?query=param"
        expected_result = "https://example.com/path/to/resource"
        result = remove_url_param(_input)
        self.assertEqual(expected_result, result)

    def test_extract_domain(self):
        _input = "https://example.com/path/to/resource"
        expected_result = "example.com"
        result = extract_domain(_input)
        self.assertEqual(expected_result, result)

    def test_extract_sub_url(self):
        _input = "https://example.com/path/to/resource"
        expected_result = "path/to/resource"
        result = extract_sub_url(_input)
        self.assertEqual(expected_result, result)

    def test_url_encode(self):
        _input = "https://zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4?AWSAccessKeyId=AKIA6QKGZHG2T5CA2K5B&Signature=863BpdtT2OdQ90v%2F50u8IB28I18%3D&Expires=1717075198"
        expected_result = "https%3A//zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4%3FAWSAccessKeyId%3DAKIA6QKGZHG2T5CA2K5B%2526Signature%3D34Vc1xf1fKuRmf2MrvKIUvktjhc%253D%2526Expires%3D1716984440"
        result = url_encode(_input)
        self.assertEqual(expected_result, result)

    def test_url_dencode(self):
        _input= "https%3A//zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4%3FAWSAccessKeyId%3DAKIA6QKGZHG2T5CA2K5B%2526Signature%3D34Vc1xf1fKuRmf2MrvKIUvktjhc%253D%2526Expires%3D1716984440"
        expected_result = "https://zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4?AWSAccessKeyId=AKIA6QKGZHG2T5CA2K5B%26Signature=34Vc1xf1fKuRmf2MrvKIUvktjhc%3D%26Expires=1716984440"
        result = url_decode(_input)
        self.assertEqual(expected_result, result)

    def test_url_codec(self):
        _input = "https://zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4?AWSAccessKeyId=AKIA6QKGZHG2T5CA2K5B%26Signature=34Vc1xf1fKuRmf2MrvKIUvktjhc%3D%26Expires=1716984440"
        expected_result = "https://zhangrj-data-analyzer.s3.amazonaws.com/report/crawl/daily_adj/20240517/Summary_Daily_AAPL-10.mp4?AWSAccessKeyId=AKIA6QKGZHG2T5CA2K5B%26Signature=34Vc1xf1fKuRmf2MrvKIUvktjhc%3D%26Expires=1716984440"
        result = url_encode(_input)
        result = url_decode(result)
        self.assertEqual(expected_result, result)
