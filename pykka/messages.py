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

from collections import namedtuple


# Internal actor messages
_ActorStop = namedtuple("ActorStop", [])

# Public proxy messages
ProxyCall = namedtuple("ProxyCall", ["attr_path", "args", "kwargs"])
ProxyCall.__doc__ = """
Message to ask the actor to call the method with the arguments.
"""
ProxyCall.attr_path.__doc__ = "List with the path from the actor to the method."
ProxyCall.args.__doc__ = "List with positional arguments."
ProxyCall.kwargs.__doc__ = "Dict with keyword arguments."

ProxyGetAttr = namedtuple("ProxyGetAttr", ["attr_path"])
ProxyGetAttr.__doc__ = """
Message to ask the actor to return the value of the attribute.
"""
ProxyGetAttr.attr_path.__doc__ = """
List with the path from the actor to the attribute.
"""

ProxySetAttr = namedtuple("ProxySetAttr", ["attr_path", "value"])
ProxySetAttr.__doc__ = """
Message to ask the actor to set the attribute to the value.
"""
ProxySetAttr.attr_path.__doc__ = """
List with the path from the actor to the attribute.
"""
ProxySetAttr.value.__doc__ = "The value to set the attribute to."
