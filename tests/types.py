from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol

if TYPE_CHECKING:
    from pykka import Actor, Future


class Event(Protocol):
    def clear(self) -> None: ...

    def is_set(self) -> bool: ...

    def set(self) -> None: ...

    def wait(self, timeout: Optional[float] = None) -> bool: ...


@dataclass
class Events:
    on_start_was_called: Event
    on_stop_was_called: Event
    on_failure_was_called: Event
    greetings_was_received: Event
    actor_registered_before_on_start_was_called: Event


@dataclass
class Runtime:
    name: str
    actor_class: type[Actor]
    event_class: type[Event]
    future_class: type[Future[Any]]
    sleep_func: Callable[[float], None]
