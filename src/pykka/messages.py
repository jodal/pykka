"""The :mod:`pykka.messages` module contains Pykka's own actor messages.

In general, you should not need to use any of these classes. However, they have
been made part of the public API so that certain optimizations can be done
without touching Pykka's internals.

An example is to combine :meth:`~pykka.ActorRef.ask` and :class:`ProxyCall`
to call a method on an actor without having to spend any resources on creating
a proxy object::

    reply = actor_ref.ask(
        ProxyCall(
            attr_path=['my_method'],
            args=['foo'],
            kwargs={'bar': 'baz'}
        )
    )

Another example is to use :meth:`~pykka.ActorRef.tell` instead of
:meth:`~pykka.ActorRef.ask` for the proxy method call, and thus avoid the
creation of a future for the return value if you don't need it.

It should be noted that these optimizations should only be necessary in very
special circumstances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Tuple

if TYPE_CHECKING:
    from pykka._types import AttrPath


class _ActorStop(NamedTuple):  # pyright: ignore[reportUnusedClass]
    """Internal message."""


class ProxyCall(NamedTuple):
    """Message to ask the actor to call the method with the arguments."""

    #: List with the path from the actor to the method.
    attr_path: AttrPath

    #: List with positional arguments.
    args: Tuple[Any, ...]

    #: Dict with keyword arguments.
    kwargs: Dict[str, Any]


class ProxyGetAttr(NamedTuple):
    """Message to ask the actor to return the value of the attribute."""

    #: List with the path from the actor to the attribute.
    attr_path: AttrPath


class ProxySetAttr(NamedTuple):
    """Message to ask the actor to set the attribute to the value."""

    #: List with the path from the actor to the attribute.
    attr_path: AttrPath

    #: The value to set the attribute to.
    value: Any
