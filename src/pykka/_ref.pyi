import threading
from typing import Any, overload

from typing_extensions import Literal  # Py38+: Available in ``typing``

from pykka import ActorProxy, Future
from pykka._actor import Actor, ActorInbox

class ActorRef:
    _actor: Actor
    actor_class: type[Actor]
    actor_urn: str
    actor_inbox: ActorInbox
    actor_stopped: threading.Event
    def __init__(self, actor: Actor) -> None: ...
    def is_alive(self) -> bool: ...
    def tell(self, message: Any) -> None: ...
    @overload
    def ask(
        self,
        message: Any,
        block: Literal[False],
        timeout: float | None = ...,
    ) -> Future[Any]: ...
    @overload  # noqa: Allow redefinition
    def ask(
        self,
        message: Any,
        block: Literal[True],
        timeout: float | None = ...,
    ) -> Any: ...
    @overload  # noqa: Allow redefinition
    def ask(
        self, message: Any, block: bool = ..., timeout: float | None = ...
    ) -> Future[Any] | Any: ...
    @overload
    def stop(self, block: Literal[True], timeout: float | None) -> bool: ...
    @overload  # noqa: Allow redefinition
    def stop(
        self, block: Literal[False], timeout: float | None = ...
    ) -> Future[bool]: ...
    @overload  # noqa: Allow redefinition
    def stop(self, block: bool, timeout: float | None = ...) -> Future[bool] | bool: ...
    def proxy(self) -> ActorProxy: ...
