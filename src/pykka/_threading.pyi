from queue import Queue
from typing import Any, ClassVar, NamedTuple, Optional

from pykka import Actor, Future
from pykka._types import OptExcInfo

class ThreadingFutureResult(NamedTuple):
    value: Optional[Any] = ...
    exc_info: Optional[OptExcInfo] = ...

class ThreadingFuture(Future):
    _queue: Queue[ThreadingFutureResult]
    _result: Optional[ThreadingFutureResult]

class ThreadingActor(Actor):
    use_deamon_thread: ClassVar[bool]
