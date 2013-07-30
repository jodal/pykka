import collections as _collections
import functools as _functools
import sys as _sys

try:
    # Python 2.x
    import Queue as _queue
    _basestring = basestring
    PY3 = False
except ImportError:
    # Python 3.x
    import queue as _queue  # noqa
    _basestring = str
    PY3 = True

from pykka.exceptions import Timeout as _Timeout


def _is_iterable(x):
    return (
        isinstance(x, _collections.Iterable) and
        not isinstance(x, _basestring))


def _map(func, *iterables):
    if len(iterables) == 1 and not _is_iterable(iterables[0]):
        return func(iterables[0])
    else:
        return list(map(func, *iterables))


class Future(object):
    """
    A :class:`Future` is a handle to a value which are available or will be
    available in the future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get`.
    """

    def __init__(self):
        super(Future, self).__init__()
        self._get_hook = None

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
        if self._get_hook is not None:
            return self._get_hook(timeout)
        raise NotImplementedError

    def set(self, value=None):
        """
        Set the encapsulated value.

        :param value: the encapsulated value or nothing
        :type value: any picklable object or :class:`None`
        :raise: an exception if set is called multiple times
        """
        raise NotImplementedError

    def set_exception(self, exc_info=None):
        """
        Set an exception as the encapsulated value.

        You can pass an ``exc_info`` three-tuple, as returned by
        :func:`sys.exc_info`. If you don't pass ``exc_info``,
        :func:`sys.exc_info` will be called and the value returned by it used.

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

    def set_get_hook(self, func):
        """
        Set a function to be executed when :meth:`get` is called.

        The function will be called when :meth:`get` is called, with the
        ``timeout`` value as the only argument. The function's return value
        will be returned from :meth:`get`.

        .. versionadded:: 1.2

        :param func: called to produce return value of :meth:`get`
        :type func: function accepting a timeout value
        """
        self._get_hook = func

    def filter(self, func):
        """
        Return a new future with only the items passing the predicate function.

        If the future's value is an iterable, :meth:`filter` will return a new
        future whose value is another iterable with only the items from the
        first iterable for which ``func(item)`` is true. If the future's value
        isn't an iterable, a :exc:`TypeError` will be raised when :meth:`get`
        is called.

        Example::

            >>> import pykka
            >>> f = pykka.ThreadingFuture()
            >>> g = f.filter(lambda x: x > 10)
            >>> g
            <pykka.future.ThreadingFuture at ...>
            >>> f.set(range(5, 15))
            >>> f.get()
            [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
            >>> g.get()
            [11, 12, 13, 14]

        .. versionadded:: 1.2
        """
        future = self.__class__()
        future.set_get_hook(lambda timeout: list(filter(
            func, self.get(timeout))))
        return future

    def join(self, *futures):
        """
        Return a new future with a list of the result of multiple futures.

        One or more futures can be passed as arguments to :meth:`join`. The new
        future returns a list with the results from all the joined futures.

        Example::

            >>> import pykka
            >>> a = pykka.ThreadingFuture()
            >>> b = pykka.ThreadingFuture()
            >>> c = pykka.ThreadingFuture()
            >>> f = a.join(b, c)
            >>> a.set('def')
            >>> b.set(123)
            >>> c.set(False)
            >>> f.get()
            ['def', 123, False]

        .. versionadded:: 1.2
        """
        future = self.__class__()
        future.set_get_hook(lambda timeout: [
            f.get(timeout) for f in [self] + list(futures)])
        return future

    def map(self, func):
        """
        Return a new future with the result of the future passed through a
        function.

        If the future's result is a single value, it is simply passed to the
        function. If the future's result is an iterable, the function is
        applied to each item in the iterable.

        Example::

            >>> import pykka
            >>> f = pykka.ThreadingFuture()
            >>> g = f.map(lambda x: x + 10)
            >>> f.set(30)
            >>> g.get()
            40

            >>> f = pykka.ThreadingFuture()
            >>> g = f.map(lambda x: x + 10)
            >>> f.set([30, 300, 3000])
            >>> g.get()
            [40, 310, 3010]

        .. versionadded:: 1.2
        """
        future = self.__class__()
        future.set_get_hook(lambda timeout: _map(func, self.get(timeout)))
        return future

    def reduce(self, func, *args):
        """
        reduce(func[, initial])

        Return a new future with the result of reducing the future's iterable
        into a single value.

        The function of two arguments is applied cumulatively to the items of
        the iterable, from left to right. The result of the first function call
        is used as the first argument to the second function call, and so on,
        until the end of the iterable. If the future's value isn't an iterable,
        a :exc:`TypeError` is raised.

        :meth:`reduce` accepts an optional second argument, which will be used
        as an initial value in the first function call. If the iterable is
        empty, the initial value is returned.

        Example::

            >>> import pykka
            >>> f = pykka.ThreadingFuture()
            >>> g = f.reduce(lambda x, y: x + y)
            >>> f.set(['a', 'b', 'c'])
            >>> g.get()
            'abc'

            >>> f = pykka.ThreadingFuture()
            >>> g = f.reduce(lambda x, y: x + y)
            >>> f.set([1, 2, 3])
            >>> (1 + 2) + 3
            6
            >>> g.get()
            6

            >>> f = pykka.ThreadingFuture()
            >>> g = f.reduce(lambda x, y: x + y, 5)
            >>> f.set([1, 2, 3])
            >>> ((5 + 1) + 2) + 3
            11
            >>> g.get()
            11

            >>> f = pykka.ThreadingFuture()
            >>> g = f.reduce(lambda x, y: x + y, 5)
            >>> f.set([])
            >>> g.get()
            5

        .. versionadded:: 1.2
        """
        future = self.__class__()
        future.set_get_hook(lambda timeout: _functools.reduce(
            func, self.get(timeout), *args))
        return future


class ThreadingFuture(Future):
    """
    :class:`ThreadingFuture` implements :class:`Future` for use with
    :class:`ThreadingActor <pykka.ThreadingActor>`.

    The future is implemented using a :class:`Queue.Queue`.

    The future does *not* make a copy of the object which is :meth:`set()
    <pykka.Future.set>` on it. It is the setters responsibility to only pass
    immutable objects or make a copy of the object before setting it on the
    future.

    .. versionchanged:: 0.14
        Previously, the encapsulated value was a copy made with
        :func:`copy.deepcopy`, unless the encapsulated value was a future, in
        which case the original future was encapsulated.
    """

    def __init__(self):
        super(ThreadingFuture, self).__init__()
        self._queue = _queue.Queue(maxsize=1)
        self._data = None

    def get(self, timeout=None):
        try:
            return super(ThreadingFuture, self).get(timeout=timeout)
        except NotImplementedError:
            pass

        try:
            if self._data is None:
                self._data = self._queue.get(True, timeout)
            if 'exc_info' in self._data:
                exc_info = self._data['exc_info']
                if PY3:
                    raise exc_info[1].with_traceback(exc_info[2])
                else:
                    exec('raise exc_info[0], exc_info[1], exc_info[2]')
            else:
                return self._data['value']
        except _queue.Empty:
            raise _Timeout('%s seconds' % timeout)

    def set(self, value=None):
        self._queue.put({'value': value}, block=False)

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
    :type futures: list of :class:`pykka.Future`

    :param timeout: seconds to wait before timeout
    :type timeout: float or :class:`None`

    :raise: :exc:`pykka.Timeout` if timeout is reached
    :returns: list of results
    """
    return [future.get(timeout=timeout) for future in futures]
