from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, Optional, TypeVar

from pykka.asyncio import AsyncioEvent, Actor, Future
from pykka import Timeout

if TYPE_CHECKING:
    from pykka.asyncio._actor import ActorInbox
    from pykka._envelope import Envelope
    from pykka._types import OptExcInfo

    __all__ = ["AsyncioActor", "AsyncioFuture"]


T = TypeVar("T")


class AsyncioFuture(Future[T]):
    """Implementation of :class:`Future` for use with async Python.

    The future is implemented using a :class:`asyncio.Future`.

    The future does *not* make a copy of the object which is :meth:`set()
    <pykka.Future.set>` on it. It is the setters responsibility to only pass
    immutable objects or make a copy of the object before setting it on the
    future.
    """

    def __init__(self) -> None:
        super().__init__()
        self._future = asyncio.get_running_loop().create_future()

    async def get(
        self,
        *,
        timeout: Optional[float] = None,
    ) -> Any:
        try:
            return await super().get(timeout=timeout)
        except NotImplementedError:
            pass

        try:
            return await asyncio.wait_for(asyncio.shield(self._future), timeout)
        except TimeoutError as e:
            msg = f"{timeout} seconds"
            raise Timeout(msg) from None


    def set(
        self,
        value: Optional[Any] = None,
    ) -> None:
        self._future.set_result(value)

    def set_exception(
        self,
        exc_info: Optional[OptExcInfo] = None,
    ) -> None:
        assert exc_info is None or len(exc_info) == 3
        if exc_info is None:
            exc_info = sys.exc_info()
        _type, e, _traceback = exc_info
        self._future.set_exception(e)


class AsyncioActor(Actor):
    """Implementation of :class:`Actor` using Python asyncio.
    """

    @staticmethod
    def _create_actor_inbox() -> ActorInbox:
        inbox: asyncio.Queue[Envelope[Any]] = asyncio.Queue()
        return inbox

    @staticmethod
    def _create_future() -> Future[Any]:
        return AsyncioFuture()

    def _start_actor_loop(self) -> None:
        self._task = asyncio.create_task(self._actor_loop(), name=self.__class__.__name__)
