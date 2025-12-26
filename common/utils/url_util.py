from urllib import parse as urllib_parse
from urllib.parse import urlparse, unquote


def check_url(file_path: str) -> bool:
    """
    Check URL from local directory path.

    :param file_path: uri to be checked
    :return: True/False
    """
    parsed = urlparse(file_path)
    if parsed.scheme and parsed.netloc:
        return True
    return False


def remove_url_param(url: str) -> str:
    """
    Extracts and returns the substring without url param

    "https://example.com/path/to/resource?query=param" -> "https://example.com/path/to/resource"

    :param url: The URL from which to extract the substring
    :return: The extracted substring
    """
    # Find the position of the last question mark
    last_question_pos = url.rfind('?')
    if last_question_pos == -1:
        last_question_pos = len(url)  # If there's no question mark, use the end of the URL

    # Extract and return the substring
    return url[: last_question_pos]


def extract_all(url: str) -> dict:
    """
    Extract all parts of the URL

    @param url:
    @return:
    """
    # Parse the URL
    parsed_url = urlparse(url)

    # Extract and return the domain
    return {
        "scheme": parsed_url.scheme,
        "domain": parsed_url.netloc,
        "path": parsed_url.path,
        "params": parsed_url.params,
        "query": parsed_url.query,
        "fragment": parsed_url.fragment,
    }


def extract_domain(url: str) -> str:
    """
    Extracts and returns the domain from the given URL

    "https://example.com/path/to/resource" -> "example.com"

    :param url: The URL from which to extract the domain
    :return: The extracted domain
    """
    # Parse the URL
    parsed_url = urlparse(url)

    # Extract and return the domain
    return parsed_url.netloc


def extract_sub_url(url: str) -> str:
    """
    Extracts and returns the substring with URL decoded

    The substirng is from the left third slash of the given URL.

    "https://example.com/path/to/resource" -> "path/to/resource"

    :param url: The URL from which to extract the substring
    :return: The extracted substring
    """
    # Find the position of the third slash
    third_slash_pos = -1
    slash_count = 0
    for i, char in enumerate(url):
        if char == '/':
            slash_count += 1
            if slash_count == 3:
                third_slash_pos = i
                break

    if third_slash_pos == -1:
        return ""  # If there aren't three slashes, return an empty string

    # Extract and return the substring
    _sub_url = url[third_slash_pos + 1:]

    # URL decode
    return unquote(_sub_url)


def url_encode(url: str):
    """
    Encode URL
    @param url:
    @return:
    """
    return urllib_parse.quote(url)


def url_decode(url: str):
    """
    Decode URL
    @param url:
    @return:
    """
    return urllib_parse.unquote(url)
