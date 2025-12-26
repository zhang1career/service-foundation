def float_digit1(num):
    """
    Format float number with 1 digits
    1 -> 1.0

    @param num:
    @return: float number with 1 digits
    """
    return "{0:.1f}".format(num)


def float_digit4(num):
    """
    Format float number with 4 digits, without tailing zeros
    1234.56000 -> 1234.5600

    @param num: number
    @return: float number with 4 digits
    """
    return "{0:.4f}".format(num)


def float_digit4_without_tailing_zeros(num):
    """
    Format float number with 4 digits, without tailing zeros
    1234.56000 -> 1234.56

    @param num: number
    @return: float number with 4 digits
    """
    return "{0:.4f}".format(num).rstrip("0").rstrip(".")
