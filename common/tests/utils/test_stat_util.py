from unittest import TestCase

from common.utils.stat_util import calculate_rising_rates


class Test(TestCase):
    def test_calculate_rising_rates(self):
        # lazy load
        import pandas as pd

        data = {
            'AAPL': [150, 152, 154],
            'GOOG': [2800, 2820, 2840],
            'MSFT': [300, 305, 310]
        }

        df = pd.DataFrame(data)

        result = calculate_rising_rates(df)
        print(result)
