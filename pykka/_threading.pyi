import threading
from queue import Queue
from typing import Any, Callable, ClassVar, NamedTuple, Optional

from pykka import Actor, Future, Scheduler
from pykka._types import OptExcInfo

class ThreadingFutureResult(NamedTuple):
    value: Optional[Any] = ...
    exc_info: Optional[OptExcInfo] = ...

class ThreadingFuture(Future):
    _queue: Queue[ThreadingFutureResult]
    _result: Optional[ThreadingFutureResult]

class ThreadingActor(Actor):
    use_deamon_thread: ClassVar[bool]

class ThreadingScheduler(Scheduler):
    @staticmethod
    def _get_timer(
        delay: float, func: Callable, *args: Any
    ) -> threading.Timer: ...
