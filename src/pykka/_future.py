from __future__ import annotations

import functools
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    cast,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from pykka._types import OptExcInfo

__all__ = ["Future", "get_all"]


T = TypeVar("T")
J = TypeVar("J")  # For when T is Iterable[J]
M = TypeVar("M")  # Result of Future.map()
R = TypeVar("R")  # Result of Future.reduce()

GetHookFunc: TypeAlias = Callable[[Optional[float]], T]


class Future(Generic[T]):
    """A handle to a value which is available now or in the future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get` or
    ``await`` the future.
    """

    _get_hook: Optional[GetHookFunc[T]]
    _get_hook_result: Optional[T]

    def __init__(self) -> None:
        super().__init__()
        self._get_hook = None
        self._get_hook_result = None

    def __repr__(self) -> str:
        return "<pykka.Future>"

    def get(
        self,
        *,
        timeout: Optional[float] = None,
    ) -> T:
        """Get the value encapsulated by the future.

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
            if self._get_hook_result is None:
                self._get_hook_result = self._get_hook(timeout)
            return self._get_hook_result
        raise NotImplementedError

    def set(
        self,
        value: Optional[T] = None,
    ) -> None:
        """Set the encapsulated value.

        :param value: the encapsulated value or nothing
        :type value: any object or :class:`None`
        :raise: an exception if set is called multiple times
        """
        raise NotImplementedError

    def set_exception(
        self,
        exc_info: Optional[OptExcInfo] = None,
    ) -> None:
        """Set an exception as the encapsulated value.

        You can pass an ``exc_info`` three-tuple, as returned by
        :func:`sys.exc_info`. If you don't pass ``exc_info``,
        :func:`sys.exc_info` will be called and the value returned by it used.

        In other words, if you're calling :meth:`set_exception`, without any
        arguments, from an except block, the exception you're currently
        handling will automatically be set on the future.

        :param exc_info: the encapsulated exception
        :type exc_info: three-tuple of (exc_class, exc_instance, traceback)
        """
        raise NotImplementedError

    def set_get_hook(
        self,
        func: GetHookFunc[T],
    ) -> None:
        """Set a function to be executed when :meth:`get` is called.

        The function will be called when :meth:`get` is called, with the
        ``timeout`` value as the only argument. The function's return value
        will be returned from :meth:`get`.

        .. versionadded:: 1.2

        :param func: called to produce return value of :meth:`get`
        :type func: function accepting a timeout value
        """
        self._get_hook = func

    def filter(
        self: Future[Iterable[J]],
        func: Callable[[J], bool],
    ) -> Future[Iterable[J]]:
        """Return a new future with only the items passing the predicate function.

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
        future.set_get_hook(
            lambda timeout: list(filter(func, self.get(timeout=timeout)))
        )
        return future

    def join(
        self: Future[Any],
        *futures: Future[Any],
    ) -> Future[Iterable[Any]]:
        """Return a new future with a list of the result of multiple futures.

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
        future = cast(Future[Iterable[Any]], self.__class__())
        future.set_get_hook(
            lambda timeout: [f.get(timeout=timeout) for f in [self, *futures]]
        )
        return future

    def map(
        self,
        func: Callable[[T], M],
    ) -> Future[M]:
        """Pass the result of the future through a function.

        Example::

            >>> import pykka
            >>> f = pykka.ThreadingFuture()
            >>> g = f.map(lambda x: x + 10)
            >>> f.set(30)
            >>> g.get()
            40

            >>> f = pykka.ThreadingFuture()
            >>> g = f.map(lambda x: x['foo'])
            >>> f.set({'foo': 'bar'}})
            >>> g.get()
            'bar'

        .. versionadded:: 1.2

        .. versionchanged:: 2.0
            Previously, if the future's result was an iterable (except a
            string), the function was applied to each item in the iterable.
            This behavior is unpredictable and makes regular use cases like
            extracting a single field from a dict difficult, thus the
            behavior has been simplified. Now, the entire result value is
            passed to the function.
        """
        future = cast(Future[M], self.__class__())
        future.set_get_hook(lambda timeout: func(self.get(timeout=timeout)))
        return future

    def reduce(
        self: Future[Iterable[J]],
        func: Callable[[R, J], R],
        *args: R,
    ) -> Future[R]:
        """Reduce a future's iterable result to a single value.

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
        future = cast(Future[R], self.__class__())
        future.set_get_hook(
            lambda timeout: functools.reduce(func, self.get(timeout=timeout), *args)
        )
        return future

    def __await__(self) -> Generator[None, None, T]:
        yield
        value = self.get()
        return value

    __iter__ = __await__


def get_all(
    futures: Iterable[Future[T]],
    *,
    timeout: Optional[float] = None,
) -> Iterable[T]:
    """Collect all values encapsulated in the list of futures.

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
