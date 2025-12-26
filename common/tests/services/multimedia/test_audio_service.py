from unittest import TestCase


from common.services.multimedia.audio_service import df_to_voice


class Test(TestCase):
    def test_df_to_voice(self):
        # lazy load
        import pandas as pd

        data = {
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [24, 27, 22],
            'City': ['New York', 'San Francisco', 'Los Angeles']
        }
        df = pd.DataFrame(data)

        df_to_voice(df, output_file='test_df_to_voice.mp3')
