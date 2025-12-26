from unittest import TestCase

from pandas import DataFrame
from pandas import to_datetime

from common.utils.df_util import extract_column_and_combine, extract_row_and_combine


class Test(TestCase):
    def test_extract_column_and_combine(self):
        df1 = DataFrame({
            "symbol": ["AAPL"] * 3,
            "close": [150, 152, 154],
            "completed_at": to_datetime(["2024-05-01", "2024-05-02", "2024-05-03"])
        })

        df2 = DataFrame({
            "symbol": ["GOOG"] * 3,
            "close": [2800, 2820, 2840],
            "completed_at": to_datetime(["2024-05-01", "2024-05-02", "2024-05-03"])
        })

        df3 = DataFrame({
            "symbol": ["MSFT"] * 3,
            "close": [300, 305, 310],
            "completed_at": to_datetime(["2024-05-01", "2024-05-02", "2024-05-03"])
        })

        # List of DataFrames
        df_list = [df1, df2, df3]

        # Extract and combine the "close" columns
        result_df = extract_column_and_combine(df_list, "symbol", "completed_at", "close")
        print(result_df)

    def test_extract_row_and_combine(self):
        df1 = DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL'],
            'close': [150, 152, 154],
            'volume': [1000, 1100, 1200]
        })
        df2 = DataFrame({
            'symbol': ['GOOG', 'GOOG', 'GOOG'],
            'close': [2800, 2820, 2840],
            'volume': [2000, 2100, 2200]
        })
        df3 = DataFrame({
            'symbol': ['MSFT', 'MSFT', 'MSFT'],
            'close': [300, 305, 310],
            'volume': [1500, 1600, 1700]
        })

        # List of DataFrames
        df_list = [df1, df2, df3]

        # Combine the last rows
        result_df = extract_row_and_combine(df_list, "symbol", -1)
        print(result_df)
