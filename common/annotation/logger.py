import time

from functools import wraps


def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        s_time = time.time()
        result = func(*args, **kwargs)
        e_time = time.time()
        print({
            'start': s_time,
            'cost': e_time - s_time
        })
        return result
    return wrapper
