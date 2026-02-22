import unittest
from unittest import TestCase

try:
    from common.services.multimedia.audio_service import df_to_voice
    _AUDIO_SKIP = None
except ImportError as e:
    df_to_voice = None
    _AUDIO_SKIP = "audio_service deps missing: %s" % e


@unittest.skipIf(df_to_voice is None, _AUDIO_SKIP or "audio_service not available")
class TestAudioService(TestCase):
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
