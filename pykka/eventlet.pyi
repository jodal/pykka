from typing import Any, Callable, Optional

import eventlet.event
import eventlet.greenthread

from pykka import Actor, Future, Scheduler


class EventletEvent(eventlet.event.Event):
    def set(self) -> None: ...
    def is_set(self) -> bool: ...
    def clear(self) -> None: ...
    def wait(self, timeout: Optional[float] = ...) -> bool: ...

class EventletFuture(Future):
    event = EventletEvent

class EventletActor(Actor): ...

class EventletScheduler(Scheduler):
    @staticmethod
    def _get_timer(delay: float, func: Callable, *args: Any) -> eventlet.greenthread.GreenThread: ...
