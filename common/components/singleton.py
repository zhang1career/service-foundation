class _Singleton(type):
    """
    A metaclass that creates a Singleton base class when called.
    The instance is identified by the super class and the arguments passed to it.
    @reference: https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-singleton-in-python
    """

    _instances = {}

    def __call__(clazz, *args, **kwargs):
        args_hash = hash(args + tuple(sorted(kwargs.items())))
        if clazz not in clazz._instances:
            clazz._instances[clazz] = {}
        if args_hash not in clazz._instances[clazz]:
            clazz._instances[clazz][args_hash] = super(_Singleton, clazz).__call__(*args, **kwargs)
        return clazz._instances[clazz][args_hash]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass
