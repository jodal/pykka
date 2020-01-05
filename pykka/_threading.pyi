from queue import Queue
from types import TracebackType
from typing import Any, ClassVar, NamedTuple, Optional, Tuple, Type

from pykka import Actor, Future

class ThreadingFutureResult(NamedTuple):
    value: Optional[Any] = ...
    exc_info: Optional[Tuple[Type[Exception], Exception, TracebackType]] = ...

class ThreadingFuture(Future):
    _queue: Queue[ThreadingFutureResult]
    _result: Optional[ThreadingFutureResult]

class ThreadingActor(Actor):
    use_deamon_thread: ClassVar[bool]
