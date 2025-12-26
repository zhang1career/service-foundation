from pandas import DataFrame

from common.exceptions.argument_exception import IllegalArgumentException
from common.utils.list_util import check_empty
from common.utils.number_util import float_digit4_without_tailing_zeros, float_digit1, float_digit4


def format_for_input(df: DataFrame,
                     columns_about_price: list = None,
                     columns_about_profit: list = None,
                     columns_about_coef: list = None):
    """
    Format for input
    divide columns about price by 10e6

    format_for_output(df, ["open", "close", "high", "low", "close_adj"], ["dividend"], ["split_coef"]

    @param df:
    @param columns_about_price: 4 digits without tailing zeros
    @param columns_about_profit: 4 digits
    @param columns_about_coef: 1 digits
    @return:
    """
    if columns_about_price is not None and not isinstance(columns_about_price, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_price"))
    if columns_about_profit is not None and not isinstance(columns_about_profit, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_profit"))
    if columns_about_coef is not None and not isinstance(columns_about_coef, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_coef"))

    if not check_empty(columns_about_price):
        for _column in columns_about_price:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_price)

    if not check_empty(columns_about_profit):
        for _column in columns_about_profit:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_profit)

    if not check_empty(columns_about_coef):
        for _column in columns_about_coef:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_coef)

    return df


def format_for_output(df: DataFrame,
                      columns_about_price: list = None,
                      columns_about_profit: list = None,
                      columns_about_coef: list = None):
    """
    Format for output
    divide columns about price by 10e6

    format_for_output(df, ["open", "close", "high", "low", "close_adj"], ["dividend"], ["split_coef"]

    @param df:
    @param columns_about_price: 4 digits without tailing zeros
    @param columns_about_profit: 4 digits
    @param columns_about_coef: 1 digits
    @return:
    """
    if columns_about_price is not None and not isinstance(columns_about_price, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_price"))
    if columns_about_profit is not None and not isinstance(columns_about_profit, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_profit"))
    if columns_about_coef is not None and not isinstance(columns_about_coef, list):
        raise IllegalArgumentException("argument {arg} should be a list".format(arg="columns_about_coef"))

    if not check_empty(columns_about_price):
        for _column in columns_about_price:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_price_to_str)

    if not check_empty(columns_about_profit):
        for _column in columns_about_profit:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_profit_to_str)

    if not check_empty(columns_about_coef):
        for _column in columns_about_coef:
            if _column in df.columns:
                df[_column] = df[_column].map(_format_coef_to_str)

    return df


def _format_price(num):
    return num / 1e6


def _format_price_to_str(num):
    return float_digit4_without_tailing_zeros(num / 1e6)


def _format_profit(num):
    return num / 1e6


def _format_profit_to_str(num):
    return float_digit4(num / 1e6)


def _format_coef(num):
    return num / 1e3


def _format_coef_to_str(num):
    return float_digit1(num / 1e3)
