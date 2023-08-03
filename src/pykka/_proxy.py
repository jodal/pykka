from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from pykka import ActorDeadError, messages
from pykka._introspection import AttrInfo, introspect_attrs

if TYPE_CHECKING:
    from pykka import Actor, ActorRef, Future
    from pykka._types import AttrPath

__all__ = ["ActorProxy"]


logger = logging.getLogger("pykka")


T = TypeVar("T")
A = TypeVar("A", bound="Actor")


class ActorProxy(Generic[A]):
    """An :class:`ActorProxy` wraps an :class:`ActorRef <pykka.ActorRef>` instance.

    The proxy allows the referenced actor to be used through regular
    method calls and field access.

    You can create an :class:`ActorProxy` from any :class:`ActorRef
    <pykka.ActorRef>`::

        actor_ref = MyActor.start()
        actor_proxy = ActorProxy(actor_ref)

    You can also get an :class:`ActorProxy` by using :meth:`proxy()
    <pykka.ActorRef.proxy>`::

        actor_proxy = MyActor.start().proxy()

    **Attributes and method calls**

    When reading an attribute or getting a return value from a method, you get
    a :class:`Future <pykka.Future>` object back. To get the enclosed value
    from the future, you must call :meth:`get() <pykka.Future.get>` on the
    returned future::

        print(actor_proxy.string_attribute.get())
        print(actor_proxy.count().get() + 1)

    If you call a method just for it's side effects and do not care about the
    return value, you do not need to accept the returned future or call
    :meth:`get() <pykka.Future.get>` on the future. Simply call the method, and
    it will be executed concurrently with your own code::

        actor_proxy.method_with_side_effect()

    If you want to block your own code from continuing while the other method
    is processing, you can use :meth:`get() <pykka.Future.get>` to block until
    it completes::

        actor_proxy.method_with_side_effect().get()

    You can also use the ``await`` keyword to block until the method completes::

        await actor_proxy.method_with_side_effect()

    If you access a proxied method as an attribute, without calling it, you
    get an :class:`CallableProxy`.

    **Proxy to itself**

    An actor can use a proxy to itself to schedule work for itself. The
    scheduled work will only be done after the current message and all messages
    already in the inbox are processed.

    For example, if an actor can split a time consuming task into multiple
    parts, and after completing each part can ask itself to start on the next
    part using proxied calls or messages to itself, it can react faster to
    other incoming messages as they will be interleaved with the parts of the
    time consuming task. This is especially useful for being able to stop the
    actor in the middle of a time consuming task.

    To create a proxy to yourself, use the actor's :attr:`actor_ref
    <pykka.Actor.actor_ref>` attribute::

        proxy_to_myself_in_the_future = self.actor_ref.proxy()

    If you create a proxy in your actor's constructor or :meth:`on_start
    <pykka.Actor.on_start>` method, you can create a nice API for deferring
    work to yourself in the future::

        def __init__(self):
            ...
            self._in_future = self.actor_ref.proxy()
            ...

        def do_work(self):
            ...
            self._in_future.do_more_work()
            ...

        def do_more_work(self):
            ...

    To avoid infinite loops during proxy introspection, proxies to self
    should be kept as private instance attributes by prefixing the attribute
    name with ``_``.

    **Examples**

    An example of :class:`ActorProxy` usage:

    .. literalinclude:: ../../examples/counter.py

    :param actor_ref: reference to the actor to proxy
    :type actor_ref: :class:`pykka.ActorRef`

    :raise: :exc:`pykka.ActorDeadError` if actor is not available
    """

    #: The actor's :class:`pykka.ActorRef` instance.
    actor_ref: ActorRef[A]

    _actor: A
    _attr_path: AttrPath
    _known_attrs: dict[AttrPath, AttrInfo]
    _actor_proxies: dict[AttrPath, ActorProxy[A]]
    _callable_proxies: dict[AttrPath, CallableProxy[A]]

    def __init__(
        self,
        *,
        actor_ref: ActorRef[A],
        attr_path: Optional[AttrPath] = None,
    ) -> None:
        if not actor_ref.is_alive():
            raise ActorDeadError(f"{actor_ref} not found")
        self.actor_ref = actor_ref
        self._actor = actor_ref._actor  # noqa: SLF001
        self._attr_path = attr_path or ()
        self._known_attrs = introspect_attrs(root=self._actor, proxy=self)
        self._actor_proxies = {}
        self._callable_proxies = {}

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, ActorProxy):
            return False
        if self._actor != other._actor:  # pyright: ignore[reportUnknownMemberType]
            return False
        if self._attr_path != other._attr_path:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self._actor, self._attr_path))

    def __repr__(self) -> str:
        return f"<ActorProxy for {self.actor_ref}, attr_path={self._attr_path!r}>"

    def __dir__(self) -> list[str]:
        result = ["__class__"]
        result += list(self.__class__.__dict__.keys())
        result += list(self.__dict__.keys())
        result += [attr_path[0] for attr_path in list(self._known_attrs.keys())]
        return sorted(result)

    def __getattr__(self, name: str) -> Any:
        """Get a field or callable from the actor."""
        attr_path: AttrPath = (*self._attr_path, name)

        if attr_path not in self._known_attrs:
            self._known_attrs = introspect_attrs(root=self._actor, proxy=self)

        attr_info = self._known_attrs.get(attr_path)
        if attr_info is None:
            raise AttributeError(f"{self} has no attribute {name!r}")

        if attr_info.callable:
            if attr_path not in self._callable_proxies:
                self._callable_proxies[attr_path] = CallableProxy(
                    actor_ref=self.actor_ref,
                    attr_path=attr_path,
                )
            return self._callable_proxies[attr_path]

        if attr_info.traversable:
            if attr_path not in self._actor_proxies:
                self._actor_proxies[attr_path] = ActorProxy(
                    actor_ref=self.actor_ref,
                    attr_path=attr_path,
                )
            return self._actor_proxies[attr_path]

        message = messages.ProxyGetAttr(attr_path=attr_path)
        return self.actor_ref.ask(message, block=False)

    def __setattr__(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Set a field on the actor.

        Blocks until the field is set to check if any exceptions was raised.
        """
        if name == "actor_ref" or name.startswith("_"):
            return super().__setattr__(name, value)
        attr_path = (*self._attr_path, name)
        message = messages.ProxySetAttr(attr_path=attr_path, value=value)
        self.actor_ref.ask(message)
        return None


class CallableProxy(Generic[A]):
    """Proxy to a single method.

    :class:`CallableProxy` instances are returned when accessing methods on a
    :class:`ActorProxy` without calling them.

    Example::

        proxy = AnActor.start().proxy()

        # Ask semantics returns a future. See `__call__()` docs.
        future = proxy.do_work()

        # Tell semantics are fire and forget. See `defer()` docs.
        proxy.do_work.defer()
    """

    actor_ref: ActorRef[A]
    _attr_path: AttrPath

    def __init__(
        self,
        *,
        actor_ref: ActorRef[A],
        attr_path: AttrPath,
    ) -> None:
        self.actor_ref = actor_ref
        self._attr_path = attr_path

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        """Call with :meth:`~pykka.ActorRef.ask` semantics.

        Returns a future which will yield the called method's return value.

        If the call raises an exception is set on the future, and will be
        reraised by :meth:`~pykka.Future.get`. If the future is left unused,
        the exception will not be reraised. Either way, the exception will
        also be logged. See :ref:`logging` for details.
        """
        message = messages.ProxyCall(
            attr_path=self._attr_path, args=args, kwargs=kwargs
        )
        return self.actor_ref.ask(message, block=False)

    def defer(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Call with :meth:`~pykka.ActorRef.tell` semantics.

        Does not create or return a future.

        If the call raises an exception, there is no future to set the
        exception on. Thus, the actor's :meth:`~pykka.Actor.on_failure` hook
        is called instead.

        .. versionadded:: 2.0
        """
        message = messages.ProxyCall(
            attr_path=self._attr_path, args=args, kwargs=kwargs
        )
        self.actor_ref.tell(message)


def traversable(obj: T) -> T:
    """Mark an actor attribute as traversable.

    The traversable marker makes the actor attribute's own methods and
    attributes available to users of the actor through an
    :class:`~pykka.ActorProxy`.

    Used as a function to mark a single attribute::

        class AnActor(pykka.ThreadingActor):
            playback = pykka.traversable(Playback())

        class Playback(object):
            def play(self):
                return True

    This function can also be used as a class decorator, making all instances
    of the class traversable::

        class AnActor(pykka.ThreadingActor):
            playback = Playback()

        @pykka.traversable
        class Playback(object):
            def play(self):
                return True

    The third alternative, and the only way in Pykka < 2.0, is to manually
    mark a class as traversable by setting the ``pykka_traversable`` attribute
    to :class:`True`::

        class AnActor(pykka.ThreadingActor):
            playback = Playback()

        class Playback(object):
            pykka_traversable = True

            def play(self):
                return True

    When the attribute is marked as traversable, its methods can be executed
    in the context of the actor through an actor proxy::

        proxy = AnActor.start().proxy()
        assert proxy.playback.play().get() is True

    .. versionadded:: 2.0
    """
    if hasattr(obj, "__slots__"):
        raise ValueError(
            "pykka.traversable() cannot be used to mark "
            "an object using slots as traversable."
        )
    obj._pykka_traversable = True  # type: ignore[attr-defined]  # noqa: SLF001
    return obj
