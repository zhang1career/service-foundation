import matplotlib
matplotlib.use('TkAgg')

from unittest import TestCase

from common.services.multimedia.image_service.decorative_image_service import plot_value_time_line, plot_daily_candlestick
from common.utils.df_util import extract_column_and_combine, extract_row_and_combine


class Test(TestCase):
    def test_plot_value_time_line(self):
        # lazy load
        import pandas as pd

        df1 = pd.DataFrame({
            "symbol": ["AAPL"] * 3,
            "close": [150, 152, 154],
            "completed_at": [1714521600, 1714608000, 1714694400]
        })

        df2 = pd.DataFrame({
            "symbol": ["GOOG"] * 3,
            "close": [2800, 2820, 2840],
            "completed_at": [1714521600, 1714608000, 1714694400]
        })

        df3 = pd.DataFrame({
            "symbol": ["MSFT"] * 3,
            "close": [300, 305, 310],
            "completed_at": [1714521600, 1714608000, 1714694400]
        })

        # List of DataFrames
        df_list = [df1, df2, df3]

        # Extract and combine the "close" columns
        result_df = extract_column_and_combine(df_list, "symbol", "completed_at", "close")

        result_df.index = pd.to_datetime(result_df.index, unit='s')
        print(result_df)

        plot_value_time_line(result_df,
                             title="Daily Adjusted",
                             subtitle="abcd",
                             footnote="1234",
                             width=8,
                             height=4,
                             output_file="value_time_line.png")


    def test_plot_daily_candlestick(self):
        # lazy load
        import pandas as pd

        df1 = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL'],
            'open': [148, 152, 156],
            'close': [150, 152, 154],
            'high': [158, 153, 155],
            'low': [145, 151, 150],
            'volume': [1000, 1100, 1200]
        })
        df2 = pd.DataFrame({
            'symbol': ['GOOG', 'GOOG', 'GOOG'],
            'open': [280, 282, 284],
            'close': [280, 282, 284],
            'high': [280, 282, 284],
            'low': [280, 282, 284],
            'volume': [2000, 2100, 2200]
        })
        df3 = pd.DataFrame({
            'symbol': ['MSFT', 'MSFT', 'MSFT'],
            'open': [300, 305, 310],
            'close': [300, 305, 310],
            'high': [300, 305, 310],
            'low': [300, 305, 310],
            'volume': [1500, 1600, 1700]
        })

        # List of DataFrames
        df_list = [df1, df2, df3]

        # Combine the last rows
        result_df = extract_row_and_combine(df_list, "symbol", -1)
        print(result_df)

        plot_daily_candlestick(result_df,
                               title="Daily Adjusted",
                               subtitle="abcd",
                               footnote="1234",
                               width=8,
                               height=4,
                               output_file="candlestick.png")

