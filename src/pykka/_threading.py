from __future__ import annotations

import queue
import sys
import threading
import time
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, TypeVar

from pykka import Actor, Future, Timeout

if TYPE_CHECKING:
    from pykka._actor import ActorInbox
    from pykka._envelope import Envelope
    from pykka._future import GetHookFunc
    from pykka._types import OptExcInfo

__all__ = ["ThreadingActor", "ThreadingFuture"]


T = TypeVar("T")


class ThreadingFutureResult(NamedTuple):
    value: Any | None = None
    exc_info: OptExcInfo | None = None


class ThreadingFuture(Future[T]):
    """Implementation of [`Future`][pykka.Future] for use with regular Python threads.

    /// warning | Mutable messages
    The future *does not* make a copy of the object which is
    [`set()`][pykka.Future.set] on it. It is the setters responsibility to
    only pass immutable objects or make a copy of the object before setting
    it on the future.
    ///

    /// note | Version changed: Pykka 0.14
    Previously, the encapsulated value was a copy made with
    [`copy.deepcopy()`][copy.deepcopy], unless the encapsulated value was a
    future, in which case the original future was encapsulated.
    ///
    """

    def __init__(self) -> None:
        super().__init__()
        self._condition: threading.Condition = threading.Condition()
        self._result: ThreadingFutureResult | None = None

    def get(
        self,
        *,
        timeout: float | None = None,
    ) -> Any:
        deadline: float | None = None if timeout is None else time.monotonic() + timeout

        with self._condition:
            try:
                return super().get(timeout=timeout)
            except NotImplementedError:
                pass

            while self._result is None:
                remaining = (
                    deadline - time.monotonic() if deadline is not None else None
                )
                if remaining is not None and remaining <= 0.0:
                    msg = f"{timeout} seconds"
                    raise Timeout(msg)
                self._condition.wait(timeout=remaining)

            if self._result.exc_info is not None:
                (exc_type, exc_value, exc_traceback) = self._result.exc_info
                assert exc_type is not None
                if exc_value is None:
                    exc_value = exc_type()
                if exc_value.__traceback__ is not exc_traceback:
                    raise exc_value.with_traceback(exc_traceback)
                raise exc_value

            return self._result.value

    def set(
        self,
        value: Any | None = None,
    ) -> None:
        with self._condition:
            if self._result is not None or self._get_hook is not None:
                raise queue.Full
            self._result = ThreadingFutureResult(value=value)
            self._condition.notify_all()

    def set_exception(
        self,
        exc_info: OptExcInfo | None = None,
    ) -> None:
        assert exc_info is None or len(exc_info) == 3
        if exc_info is None:
            exc_info = sys.exc_info()

        with self._condition:
            if self._result is not None or self._get_hook is not None:
                raise queue.Full
            self._result = ThreadingFutureResult(exc_info=exc_info)
            self._condition.notify_all()

    def set_get_hook(
        self,
        func: GetHookFunc[T],
    ) -> None:
        with self._condition:
            if self._result is not None:
                raise queue.Full
            super().set_get_hook(func)
            self._condition.notify_all()


class ThreadingActor(Actor):
    """Implementation of [`Actor`][pykka.Actor] using regular Python threads."""

    use_daemon_thread: ClassVar[bool] = False
    """
    A boolean value indicating whether this actor is executed on a thread that
    is a daemon thread (`True`) or not (`False`). This must be set before
    [`Actor.start()`][pykka.Actor.start] is called, otherwise
    [`RuntimeError`][RuntimeError] is raised.

    The entire Python program exits when no alive non-daemon threads are left.
    This means that an actor running on a daemon thread may be interrupted at
    any time, and there is no guarantee that cleanup will be done or that
    [`Actor.on_stop()`][pykka.Actor.on_stop] will be called.

    Actors do not inherit the daemon flag from the actor that made it. It
    always has to be set explicitly for the actor to run on a daemonic thread.
    """

    @staticmethod
    def _create_actor_inbox() -> ActorInbox:
        inbox: queue.Queue[Envelope[Any]] = queue.Queue()
        return inbox

    @staticmethod
    def _create_future() -> Future[Any]:
        return ThreadingFuture()

    def _start_actor_loop(self) -> None:
        thread = threading.Thread(target=self._actor_loop)
        thread.name = thread.name.replace("Thread", self.__class__.__name__)
        thread.daemon = self.use_daemon_thread
        thread.start()
