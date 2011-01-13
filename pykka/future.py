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

    def get(self, timeout=None):
        """
        Get the value encapsulated by the future.

        Will block until the value is available, unless the optional *timeout*
        argument is set to:

        - :class:`None` -- block forever (default)
        - :class:`False` -- return immediately
        - numeric -- timeout after given number of seconds
        """
        if timeout is False:
            poll_args = []
        else:
            poll_args = [timeout]
        if self.connection.poll(*poll_args):
            return self.connection.recv()
        else:
            return None

    def wait(self, timeout=None):
        """
        Block until the future is available.

        An alias for :meth:`get`, but with a name that is more describing if
        you do not care about the return value.
        """
        return self.get(timeout)


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
