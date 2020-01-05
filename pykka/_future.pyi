from types import TracebackType
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

_T = TypeVar("_T")
I = TypeVar("I")  # For when T is Iterable[I]  # noqa

_M = TypeVar("_M")  # For Future.map()
_R = TypeVar("_R")  # For Future.reduce()

ExcInfo = Tuple[Type[Exception], Exception, TracebackType]

GetHookFunc = Callable[[Optional[float]], _T]

class Future(Generic[_T]):
    _get_hook: Optional[GetHookFunc]
    _get_hook_result: Optional[_T]
    def get(self, timeout: Optional[float] = ...) -> _T: ...
    def set(self, value: Optional[_T] = ...) -> None: ...
    def set_exception(self, exc_info: Optional[ExcInfo] = ...) -> None: ...
    def set_get_hook(self, func: GetHookFunc) -> None: ...
    def filter(
        self: Future[Iterable[I]], func: Callable[[I], bool]
    ) -> Future[Iterable[I]]: ...
    def join(self, *futures: Future[Any]) -> Future[Iterable[Any]]: ...
    def map(self, func: Callable[[_T], _M]) -> Future[_M]: ...
    def reduce(
        self: Future[Iterable[I]], func: Callable[[_R, I], _R], *args: _R
    ) -> Future[_R]: ...
    def __await__(self) -> Generator[None, None, _T]: ...

def get_all(
    futures: Iterable[Future[Any]], timeout: Optional[float] = ...
) -> Iterable[Any]: ...
