from typing import (
    Any,
    Callable,
    Dict,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from pykka import Actor, ActorRef, Future

AttrPath = Sequence[str]

class AttrInfo(NamedTuple):
    callable: bool
    traversable: bool

class ActorProxy:
    actor_ref: ActorRef
    _actor: Actor
    _attr_path: AttrPath
    _known_attrs: Dict[AttrPath, AttrInfo]
    _actor_proxies: Dict[AttrPath, ActorProxy]
    _callable_proxies: Dict[AttrPath, CallableProxy]
    def __init__(
        self, actor_ref: ActorRef, attr_path: Optional[AttrPath] = ...
    ) -> None: ...
    def _introspect_attributes(self) -> Dict[AttrPath, AttrInfo]: ...
    def _is_exposable_attribute(self, attr_name: str) -> bool: ...
    def _is_self_proxy(self, attr: Any) -> bool: ...
    def _is_callable_attribute(self, attr: Any) -> bool: ...
    def _is_traversable_attribute(self, attr: Any) -> bool: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __dir__(self) -> Dict[str, Any]: ...
    def __getattr__(
        self, name: str
    ) -> Union[CallableProxy, ActorProxy, Future[Any]]: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class CallableProxy:
    actor_ref: ActorRef
    _attr_path: AttrPath
    def __init__(self, actor_ref: ActorRef, attr_path: AttrPath) -> None: ...
    def __call__(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Future[Any]: ...
    def defer(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None: ...

FuncType = Callable[..., Any]
_F = TypeVar("_F", bound=FuncType)

def traversable(obj: _F) -> _F: ...
