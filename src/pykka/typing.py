"""The :mod:`pykka.typing` module contains helpers to improve type hints.

Since Pykka 4.0, Pykka has complete type hints for the public API, tested using
both `Mypy <https://www.mypy-lang.org/>`_ and `Pyright
<https://github.com/microsoft/pyright>`_.

Due to the dynamic nature of :class:`~pykka.ActorProxy` objects, it is not
possible to automatically type them correctly. This module contains helpers to
manually create additional classes that correctly describe the type hints for
the proxy objects. In cases where a proxy objects is used a lot, this might be
worth the extra effort to increase development speed and catch bugs earlier.

Example usage::

    from typing import cast

    from pykka import ActorProxy, ThreadingActor
    from pykka.typing import ActorMemberMixin, proxy_field, proxy_method


    class CircleActor(ThreadingActor):
        pi = 3.14

        def area(self, radius: float) -> float:
            return self.pi * radius**2


    class CircleProxy(ActorMemberMixin, ActorProxy[CircleActor]):
        pi = proxy_field(CircleActor.pi)
        area = proxy_method(CircleActor.area)


    proxy = cast(CircleProxy, CircleActor.start().proxy())

    reveal_type(proxy.stop)
    # Revealed type is 'Callable[[], pykka.Future[None]]'

    reveal_type(proxy.pi)
    # Revealed type is 'pykka.Future[float]'

    reveal_type(proxy.area))
    # Revealed type is 'Callable[[float], pykka.Future[float]]'
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Generic, Protocol, TypeVar

from pykka import Actor

if TYPE_CHECKING:
    from pykka import Future

if sys.version_info >= (3, 10):
    from typing import (
        Concatenate,
        ParamSpec,
    )
else:
    from typing_extensions import (
        Concatenate,
        ParamSpec,
    )

__all__ = [
    "ActorMemberMixin",
    "proxy_field",
    "proxy_method",
]


T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R", covariant=True)


class Method(Protocol, Generic[P, R]):
    def __get__(self, instance: Any, owner: type | None = None) -> Callable[P, R]:
        ...

    def __call__(self, obj: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


def proxy_field(field: T) -> Future[T]:
    """Type a field on an actor proxy.

    .. versionadded:: 4.0
    """
    return field  # type: ignore[return-value]


def proxy_method(
    field: Callable[Concatenate[Any, P], T],
) -> Method[P, Future[T]]:
    """Type a method on an actor proxy.

    .. versionadded:: 4.0
    """
    return field  # type: ignore[return-value]


class ActorMemberMixin:
    """Mixin class for typing actor members accessible through a proxy.

    .. versionadded:: 4.0
    """

    stop = proxy_method(Actor.stop)
    on_start = proxy_method(Actor.on_start)
    on_stop = proxy_method(Actor.on_stop)
    on_failure = proxy_method(Actor.on_failure)
    on_receive = proxy_method(Actor.on_receive)
