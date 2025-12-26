import os
from unittest import TestCase

import imageio
from PIL import Image

WORK_SPACE = "./"
GIF_FILE_NAME = "Summary_Daily_mag_7.gif"

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 400


class Test(TestCase):

    def test_gif(self):
        image_list = []
        for image_file in sorted(os.listdir(WORK_SPACE)):
            if not image_file.endswith(".png") and not image_file.endswith(".jpg"):
                continue
            image_path = os.path.join(WORK_SPACE, image_file)
            image = Image.open(image_path).resize((IMAGE_WIDTH, IMAGE_HEIGHT))
            image_list.append(image)

        duration = 1 / len(image_list)
        _gif_path = os.path.join(WORK_SPACE, GIF_FILE_NAME)
        imageio.mimsave(_gif_path, image_list, duration=duration*1000)
