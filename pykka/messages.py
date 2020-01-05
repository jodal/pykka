"""
The :mod:`pykka.messages` module contains Pykka's own actor messages.

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

from typing import Any, Dict, NamedTuple, Sequence, Tuple


class _ActorStop(NamedTuple):
    """Internal message."""

    pass


class ProxyCall(NamedTuple):
    """Message to ask the actor to call the method with the arguments."""

    #: List with the path from the actor to the method.
    attr_path: Sequence[str]

    #: List with positional arguments.
    args: Tuple[Any]

    #: Dict with keyword arguments.
    kwargs: Dict[str, Any]


class ProxyGetAttr(NamedTuple):
    """Message to ask the actor to return the value of the attribute."""

    #: List with the path from the actor to the attribute.
    attr_path: Sequence[str]


class ProxySetAttr(NamedTuple):
    """Message to ask the actor to set the attribute to the value."""

    #: List with the path from the actor to the attribute.
    attr_path: Sequence[str]

    #: The value to set the attribute to.
    value: Any
