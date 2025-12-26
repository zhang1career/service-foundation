import logging
import os

import imageio
from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 400


def image_to_gif(work_space, play_time, output_file="output.gif") -> int:
    """
    Convert audio and images to gif

    @param work_space: the working directory, holding image files
    @param play_time: time length to play
    @param output_file: the result gif's filepath
    @return: flame number
    """
    image_list = []
    for image_file in sorted(os.listdir(work_space)):
        if not image_file.endswith(".png") and not image_file.endswith(".jpg"):
            continue
        image_path = os.path.join(work_space, image_file)
        image = Image.open(image_path).resize((IMAGE_WIDTH, IMAGE_HEIGHT))
        image_list.append(image)

    duration = play_time / len(image_list)
    imageio.mimsave(output_file, image_list, duration=duration * 1000)

    return len(image_list)
