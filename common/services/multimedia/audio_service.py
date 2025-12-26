import logging

from gtts import gTTS
from pandas import DataFrame

logger = logging.getLogger(__name__)


def df_to_voice(df: DataFrame, language="en", output_file="output.mp3"):
    """
    Convert a DataFrame into speech and save it as an MP3 file.

    :param df: The input DataFrame.
    :param language: The language for the text-to-speech conversion (default is "en").
    :param output_file: The name of the output MP3 file (default is "output.mp3").
    """
    # Convert DataFrame to string
    df_str = df.to_string(index=False)

    str_to_voice(df_str, language, output_file)


def str_to_voice(data_str: str, language="en", output_file="output.mp3"):
    """
    Convert a string into speech and save it as an MP3 file.

    :param data_str: The input string.
    :param language: The language for the text-to-speech conversion (default is "en").
    :param output_file: The name of the output MP3 file (default is "output.mp3").
    """
    logger.info("[str_to_voice] param data_str=%s, language=%s, output_file=%s",
                data_str, language, output_file)
    
    # Create gTTS object
    tts = gTTS(text=data_str, lang=language)

    # Save the converted audio to an MP3 file
    tts.save(output_file)
