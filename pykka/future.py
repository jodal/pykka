import gevent

class Future(object):
    """
    A :class:`Future` is a handle to a value which will be available in the
    future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get()`.
    """
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return str(self.get())

    def get(self, block=True, timeout=None):
        """
        Get the value encapsulated by the future.

        If *block* is :class:`True`, it will block until the value is available
        or the *timeout* in seconds is reached.

        If *block* is :class:`False` it will immediately return the value if
        available or None if not.
        """
        try:
            return self.connection.get(block, timeout)
        except gevent.Timeout:
            return None

    def wait(self, timeout=None):
        """
        Block until the future is available.

        An alias for :meth:`get`, but with a name that is more describing if
        you do not care about the return value.
        """
        return self.get(timeout=timeout)


def get_all(futures, timeout=None):
    """
    Get all the values encapsulated by the given futures.

    :attr:`timeout` has the same behaviour as for :meth:`Future.get`.
    """
    return map(lambda future: future.wait(timeout), futures)


def wait_all(futures, timeout=None):
    """
    Block until all the given features are available.

    An alias for :func:`get_all`, but with a name that is more describing if
    you do not care about the return values.
    """
    return get_all(futures, timeout)
