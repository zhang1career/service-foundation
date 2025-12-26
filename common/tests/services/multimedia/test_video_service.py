import os
from unittest import TestCase

from moviepy import editor

WORK_SPACE = "./"
GIF_FILE_NAME = "Summary_Daily_mag_7.gif"
MP4_FILE_NAME = "video.mp4"

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 400
VIDEO_CODEC_LIBX264 = "libx264"
VIDEO_BITRATE_1024k = "1024k"
ENCODING_SPEED_SLOW = "slow"
CRF_20 = "20"
PIXEL_FORMAT_YUV420P = "yuv420p"
PIXEL_SCALE = "{width}:{height}".format(width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
AUDIO_CODEC_AAC = "aac"
AUDIO_BITRATE_128k = "128k"
AUDIO_CHANNEL_2 = "2"
STRICT_EXPERIMENTAL = "-2"
MOV_FLAG_FAST_START = "faststart"


class Test(TestCase):

    def test_gif_movie(self):
        _gif_path = os.path.join(WORK_SPACE, GIF_FILE_NAME)
        _video = editor.VideoFileClip(_gif_path)
        _video.write_videofile(fps=3,
                               codec=VIDEO_CODEC_LIBX264,
                               bitrate=VIDEO_BITRATE_1024k,
                               preset=ENCODING_SPEED_SLOW,
                               audio_codec=AUDIO_CODEC_AAC,
                               audio_bitrate=AUDIO_BITRATE_128k,
                               ffmpeg_params=["-crf", CRF_20,
                                              "-vf", "format=" + PIXEL_FORMAT_YUV420P,
                                              "-vf", "scale=" + PIXEL_SCALE,
                                              "-movflags", "+" + MOV_FLAG_FAST_START,
                                              ],
                               threads=1,
                               filename=MP4_FILE_NAME)
