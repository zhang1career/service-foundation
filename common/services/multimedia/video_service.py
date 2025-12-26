import logging
import subprocess

from moviepy import editor

from common.exceptions.shell_exception import ShellException
from common.utils.string_util import implode
from data_analyzer import settings

logger = logging.getLogger(__name__)

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 400

VIDEO_CODEC_LIBX264 = "libx264"
VIDEO_BITRATE_1024k = "1024k"
SAMPLE_FRAMERATE_1 = "1"
VIDEO_FPS_24 = 24
ENCODING_SPEED_SLOW = "slow"
CRF_20 = "20"
PIXEL_FORMAT_YUV420P = "yuv420p"
PIXEL_SCALE = "{width}:{height}".format(width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
AUDIO_CODEC_AAC = "aac"
AUDIO_BITRATE_128k = "128k"
AUDIO_CHANNEL_2 = "2"
STRICT_EXPERIMENTAL = "-2"
MOV_FLAG_FAST_START = "faststart"


def audio_image_to_video_by_ffmpeg(image_path, audio_path, output_file="output.mp4"):
    """
    Convert audio and images to video

    @param image_path:
    @param audio_path:
    @param output_file: the result video's filepath
    """
    command = build_command(image_path, audio_path, output_file)
    _run_command(command)


def build_command(image_path: str, audio_path: str, output_file: str):
    commands_list = [
        "ffmpeg",
        "-y", output_file,
        "-i", image_path,
        "-i", audio_path,
        "-c:v", VIDEO_CODEC_LIBX264,
        "-crf", CRF_20,
        "-preset", ENCODING_SPEED_SLOW,
        "-c:a", AUDIO_CODEC_AAC,
        "-ac", AUDIO_CHANNEL_2,
        "-vf", "format=" + PIXEL_FORMAT_YUV420P,
        "-vf", "scale=" + PIXEL_SCALE,
        "-strict", STRICT_EXPERIMENTAL,
        "-movflags", "+" + MOV_FLAG_FAST_START,
        "-r", str(VIDEO_FPS_24),
    ]

    return commands_list


def _run_command(cmd_list: list):
    logger.info("[command] param cmd=%s", implode(cmd_list, " "))

    with open("/var/log/project/data-analyzer/cmd.log", "w") as f:
        try:
            subprocess.check_call(cmd_list, stderr=f)
        except subprocess.CalledProcessError as e:
            raise ShellException("ffmpeg runs failed, msg={msg}".format(msg=e.args[0]))


def audio_gif_to_video(audio_path, gif_path, flame_number=1, output_file="output.mp4"):
    """
    Convert audio and gif to video

    @param audio_path: audio file
    @param gif_path: gif file
    @param flame_number: the gif's count of flame
    @param output_file: the result video's filepath
    """
    _audio = editor.AudioFileClip(audio_path)
    _video = editor.VideoFileClip(gif_path)
    video = _video.set_audio(_audio)
    video.write_videofile(fps=flame_number,
                          codec=VIDEO_CODEC_LIBX264,
                          bitrate=VIDEO_BITRATE_1024k,
                          preset=ENCODING_SPEED_SLOW,
                          audio_codec=AUDIO_CODEC_AAC,
                          audio_bitrate=AUDIO_BITRATE_128k,
                          ffmpeg_params=["-crf", CRF_20,
                                         "-vf", "format=" + PIXEL_FORMAT_YUV420P,
                                         "-vf", "scale=" + PIXEL_SCALE,
                                         "-movflags", "+" + MOV_FLAG_FAST_START],
                          threads=settings.THREAD,
                          logger=None,
                          filename=output_file)
