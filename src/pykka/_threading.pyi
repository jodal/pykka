from queue import Queue
from typing import Any, ClassVar, NamedTuple

from pykka import Actor, Future
from pykka._types import OptExcInfo

class ThreadingFutureResult(NamedTuple):
    value: Any | None = ...
    exc_info: OptExcInfo | None = ...

class ThreadingFuture(Future):
    _queue: Queue[ThreadingFutureResult]
    _result: ThreadingFutureResult | None

class ThreadingActor(Actor):
    use_deamon_thread: ClassVar[bool]
