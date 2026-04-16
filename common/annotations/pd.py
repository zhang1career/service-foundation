def check_input(fn):
    from pandas import Series, DataFrame
    from numpy import array as np_array

    def wrapper(_s, *args, **kwargs):
        if not isinstance(_s, (Series, DataFrame, np_array)):
            raise TypeError()
        return fn(_s, *args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper
