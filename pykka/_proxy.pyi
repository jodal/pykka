from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from pykka import Actor, ActorRef, Future
from pykka._actor import _A

_P = TypeVar("_P")  # Type at the end of the attr_path

AttrPath = Sequence[str]

class AttrInfo(NamedTuple):
    callable: bool
    traversable: bool

class ActorProxy(Generic[_A, _P]):
    actor_ref: ActorRef[_A]
    _actor: Actor[_A]
    _attr_path: AttrPath
    _known_attrs: Dict[AttrPath, AttrInfo]
    _actor_proxies: Dict[AttrPath, ActorProxy[_A, Any]]
    _callable_proxies: Dict[AttrPath, CallableProxy[_A, Any]]
    def __init__(
        self, actor_ref: ActorRef[_A], attr_path: Optional[AttrPath] = ...
    ) -> None: ...
    def _introspect_attributes(self) -> Dict[AttrPath, AttrInfo]: ...
    def _is_exposable_attribute(self, attr_name: str) -> bool: ...
    def _is_self_proxy(self, attr: Any) -> bool: ...
    def _is_callable_attribute(self, attr: Any) -> bool: ...
    def _is_traversable_attribute(self, attr: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __dir__(self) -> Dict[str, Any]: ...
    def __getattr__(
        self, name: str
    ) -> Union[CallableProxy[_A, Any], ActorProxy[_A, Any], Future[Any]]: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class CallableProxy(Generic[_A, _P]):
    actor_ref: ActorRef[_A]
    _attr_path: AttrPath
    def __init__(
        self, actor_ref: ActorRef[_A], attr_path: AttrPath
    ) -> None: ...
    def __call__(
        self, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Future[Any]: ...
    def defer(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None: ...

FuncType = Callable[..., Any]
_F = TypeVar("_F", bound=FuncType)

def traversable(obj: _F) -> _F: ...
