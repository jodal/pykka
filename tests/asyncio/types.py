from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from pykka.asyncio import AsyncioActor, AsyncioEvent, AsyncioFuture


@dataclass
class Events:
    on_start_was_called: AsyncioEvent
    on_stop_was_called: AsyncioEvent
    on_failure_was_called: AsyncioEvent
    greetings_was_received: AsyncioEvent
    actor_registered_before_on_start_was_called: AsyncioEvent


@dataclass
class Runtime:
    name: str
    actor_class: type[AsyncioActor]
    event_class: type[AsyncioEvent]
    future_class: type[AsyncioFuture[Any]]
    sleep_func: Callable[[float], Awaitable[None]]
