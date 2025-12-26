import logging

from common.exceptions.argument_exception import IllegalArgumentException
from common.utils.url_util import extract_domain

logger = logging.getLogger(__name__)


class WebPageContentCrawler:

    _domain_map = {
        "semiengineering.com": "_crawl_semiengineering_com",
    }

    def dispatch(self, url: str):
        domain = extract_domain(url)
        if not domain or domain not in self._domain_map:
            raise IllegalArgumentException("domain not supported. domain={domain}".format(domain=domain))
        func_name = self._domain_map[domain]
        return getattr(self, func_name)(url)

    def _crawl_semiengineering_com(self, url: str):
        # lazy load
        import requests

        response = requests.get(url)
        if not response.ok:
            logger.warning("[crawl_semiengineering_com] response is not ok. url=%s", url)
            return []

        # lazy load
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        article_list = soup.findAll("div", attrs={"class": "post_cnt"})
        if not article_list:
            logger.warning("[crawl_semiengineering_com] no content found. url=%s", url)
            return []

        paragraph_list = []
        for article in article_list:
            _paragraph_list = [paragraph.get_text() for paragraph in article.find_all("p")]
            if not _paragraph_list:
                continue
            paragraph_list += _paragraph_list

        return paragraph_list
