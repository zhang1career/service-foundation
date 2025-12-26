import os

from data_analyzer.settings import BASE_DIR


def app_path(sub_path):
    return os.path.join(BASE_DIR, sub_path)
