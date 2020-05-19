from typing import Any, Callable

import gevent.event
from gevent import Greenlet

from pykka import Actor, Future, Scheduler


class GeventFuture(Future):
    async_result: gevent.event.AsyncResult

class GeventActor(Actor): ...

class GeventScheduler(Scheduler):
    @staticmethod
    def _get_timer(delay: float, func: Callable, *args: Any) -> Greenlet: ...
