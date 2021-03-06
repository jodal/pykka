import queue
import sys
import threading
from typing import Any, NamedTuple, Optional

from pykka import Actor, Future, Timeout
from pykka._types import OptExcInfo

__all__ = ["ThreadingActor", "ThreadingFuture"]


class ThreadingFutureResult(NamedTuple):
    value: Optional[Any] = None
    exc_info: Optional[OptExcInfo] = None


class ThreadingFuture(Future):
    """
    :class:`ThreadingFuture` implements :class:`Future` for use with
    :class:`ThreadingActor <pykka.ThreadingActor>`.

    The future is implemented using a :class:`queue.Queue`.

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
        super().__init__()
        self._queue = queue.Queue(maxsize=1)
        self._result = None

    def get(self, timeout=None):
        try:
            return super().get(timeout=timeout)
        except NotImplementedError:
            pass

        try:
            if self._result is None:
                self._result = self._queue.get(True, timeout)
            if self._result.exc_info is not None:
                (exc_type, exc_value, exc_traceback) = self._result.exc_info
                if exc_value is None:
                    exc_value = exc_type()
                if exc_value.__traceback__ is not exc_traceback:
                    raise exc_value.with_traceback(exc_traceback)
                raise exc_value
            else:
                return self._result.value
        except queue.Empty:
            raise Timeout(f"{timeout} seconds")

    def set(self, value=None):
        self._queue.put(ThreadingFutureResult(value=value), block=False)

    def set_exception(self, exc_info=None):
        assert exc_info is None or len(exc_info) == 3
        if exc_info is None:
            exc_info = sys.exc_info()
        self._queue.put(ThreadingFutureResult(exc_info=exc_info))


class ThreadingActor(Actor):
    """
    :class:`ThreadingActor` implements :class:`Actor` using regular Python
    threads.
    """

    use_daemon_thread = False
    """
    A boolean value indicating whether this actor is executed on a thread that
    is a daemon thread (:class:`True`) or not (:class:`False`). This must be
    set before :meth:`pykka.Actor.start` is called, otherwise
    :exc:`RuntimeError` is raised.

    The entire Python program exits when no alive non-daemon threads are left.
    This means that an actor running on a daemon thread may be interrupted at
    any time, and there is no guarantee that cleanup will be done or that
    :meth:`pykka.Actor.on_stop` will be called.

    Actors do not inherit the daemon flag from the actor that made it. It
    always has to be set explicitly for the actor to run on a daemonic thread.
    """

    @staticmethod
    def _create_actor_inbox():
        return queue.Queue()

    @staticmethod
    def _create_future():
        return ThreadingFuture()

    def _start_actor_loop(self):
        thread = threading.Thread(target=self._actor_loop)
        thread.name = thread.name.replace("Thread", self.__class__.__name__)
        thread.daemon = self.use_daemon_thread
        thread.start()
