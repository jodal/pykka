import sys as _sys

try:
    # Python 2.x
    import Queue as _queue
    PY3 = False
except ImportError:
    # Python 3.x
    import queue as _queue  # pylint: disable = F0401
    PY3 = True

from pykka import Timeout as _Timeout


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
        seconds, and then raise :exc:`pykka.Timeout`.

        The encapsulated value can be retrieved multiple times. The future will
        only block the first time the value is accessed.

        :param timeout: seconds to wait before timeout
        :type timeout: float or :class:`None`

        :raise: :exc:`pykka.Timeout` if timeout is reached
        :raise: encapsulated value if it is an exception
        :return: encapsulated value if it is not an exception
        """
        raise NotImplementedError

    def set(self, value=None):
        """
        Set the encapsulated value.

        :param value: the encapsulated value or nothing
        :type value: any picklable object or :class:`None`
        """
        raise NotImplementedError

    def set_exception(self, exc_info=None):
        """
        Set an exception as the encapsulated value.

        You can pass an ``exc_info`` three-tuple, as returned by
        :func:`sys.exc_info`. If you don't pass ``exc_info``,
        ``sys.exc_info()`` will be called and the value returned by it used.

        In other words, if you're calling :meth:`set_exception`, without any
        arguments, from an except block, the exception you're currently
        handling will automatically be set on the future.

        .. versionchanged:: 0.15
            Previously, :meth:`set_exception` accepted an exception
            instance as its only argument. This still works, but it is
            deprecated and will be removed in a future release.

        :param exc_info: the encapsulated exception
        :type exc_info: three-tuple of (exc_class, exc_instance, traceback)
        """
        raise NotImplementedError


class ThreadingFuture(Future):
    """
    :class:`ThreadingFuture` implements :class:`Future` for use with
    :class:`ThreadingActor <pykka.actor.ThreadingActor>`.

    The future is implemented using a :class:`Queue.Queue`.

    The future does *not* make a copy of the object which is :meth:`set` on it.
    It is the setters responsibility to only pass immutable objects or make a
    copy of the object before setting it on the future.

    .. versionchanged:: 0.14
        Previously, the encapsulated value was a copy made with
        :func:`copy.deepcopy`, unless the encapsulated value was a future, in
        which case the original future was encapsulated.
    """

    def __init__(self):
        super(ThreadingFuture, self).__init__()
        self._queue = _queue.Queue()
        self._data = None

    def get(self, timeout=None):
        try:
            if self._data is None:
                self._data = self._queue.get(True, timeout)
            if 'exc_info' in self._data:
                exc_info = self._data['exc_info']
                if PY3:
                    raise exc_info[1].with_traceback(exc_info[2])
                else:
                    exec( # pylint: disable = W0122
                        'raise exc_info[0], exc_info[1], exc_info[2]')
            else:
                return self._data['value']
        except _queue.Empty:
            raise _Timeout('%s seconds' % timeout)

    def set(self, value=None):
        self._queue.put({'value': value})

    def set_exception(self, exc_info=None):
        if isinstance(exc_info, BaseException):
            exc_info = (exc_info.__class__, exc_info, None)
        self._queue.put({'exc_info': exc_info or _sys.exc_info()})


def get_all(futures, timeout=None):
    """
    Collect all values encapsulated in the list of futures.

    If ``timeout`` is not :class:`None`, the method will wait for a reply for
    ``timeout`` seconds, and then raise :exc:`pykka.Timeout`.

    :param futures: futures for the results to collect
    :type futures: list of `pykka.future.Future`

    :param timeout: seconds to wait before timeout
    :type timeout: float or :class:`None`

    :raise: :exc:`pykka.Timeout` if timeout is reached
    :returns: list of results
    """
    return [future.get(timeout=timeout) for future in futures]
