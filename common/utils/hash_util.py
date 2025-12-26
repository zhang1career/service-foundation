import hashlib


def md5(data: str) -> str:
    """
    Calculates the MD5 hash of a string.

    @param data: The string to be hashed
    @return: The MD5 hash of the string
    """
    _md5 = hashlib.md5()
    _md5.update(data.encode())

    return _md5.hexdigest()
