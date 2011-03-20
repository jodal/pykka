import copy

try:
    # Python 2.x
    import Queue as queue
except ImportError:
    # Python 3.x
    import queue  # pylint: disable = F0401


class Timeout(Exception):
    pass


class Future(object):
    """
    A :class:`Future` is a handle to a value which are available or will be
    available in the future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get`.
    """

    def get(self, timeout=None):
        """
        Get the value encapsulated by the future.

        If the encapsulated value is an exception, it is raised instead of
        returned.

        If ``timeout`` is :class:`None`, as default, the method will block
        until it gets a reply, potentially forever. If ``timeout`` is an
        integer or float, the method will wait for a reply for ``timeout``
        seconds, and then raise :exc:`Timeout`.

        The encapsulated value can be retrieved multiple times. The future will
        only block the first time the value is accessed.

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout
        :type timeout: float or :class:`None`

        :return: encapsulated value
        """
        raise NotImplementedError

    def set(self, value=None):
        """
        Set the encapsulated value.

        :param value: the encapsulated value or nothing
        :type value: any picklable object or :class:`None`
        """
        raise NotImplementedError

    def set_exception(self, exception):
        """
        Set an exception as the encapsulated value.

        :param exception: the encapsulated exception
        :type exception: exception
        """
        raise NotImplementedError


class ThreadingFuture(Future):
    """
    :class:`ThreadingFuture` implements :class:`Future` for use with
    :class:`pykka.actor.ThreadingActor`.

    The future is implemented using a :class:`Queue.Queue`.

    The encapsulated value is a copy made with :func:`copy.deepcopy`, unless
    the encapsulated value is another :class:`ThreadingFuture`, in which case
    the original future is encapsulated.
    """

    def __init__(self):
        super(ThreadingFuture, self).__init__()
        self._queue = queue.Queue()
        self._value_received = False
        self._value = None

    def get(self, timeout=None):
        try:
            if not self._value_received:
                self._value = self._queue.get(True, timeout)
                self._value_received = True
            if isinstance(self._value, BaseException):
                raise self._value  # pylint: disable = E0702
            else:
                return self._value
        except queue.Empty:
            raise Timeout('%s seconds' % timeout)

    def set(self, value=None):
        if isinstance(value, ThreadingFuture):
            value = value
        else:
            value = copy.deepcopy(value)
        self._queue.put(value)

    def set_exception(self, exception):
        self.set(exception)


def get_all(futures, timeout=None):
    """
    Collect all values encapsulated in the list of futures.

    If ``timeout`` is not :class:`None`, the method will wait for a reply for
    ``timeout`` seconds, and then raise :exc:`pykka.future.Timeout`.

    :param futures: futures for the results to collect
    :type futures: list of `pykka.future.Future`

    :param timeout: seconds to wait before timeout
    :type timeout: float or :class:`None`

    :returns: list of results
    """
    return [future.get(timeout=timeout) for future in futures]
