from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Optional,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from pykka.asyncio import Actor, ActorRef

__all__ = ["ActorRegistry"]


logger = logging.getLogger("pykka")


A = TypeVar("A", bound="Actor")


class ActorRegistry:
    """Registry which provides easy access to all running actors.

    Contains global state, but should be thread-safe.
    """

    _actor_refs: ClassVar[list[ActorRef[Any]]] = []

    @classmethod
    def broadcast(
        cls,
        message: Any,
        target_class: Union[str, type[Actor], None] = None,
    ) -> None:
        """Broadcast ``message`` to all actors of the specified ``target_class``.

        If no ``target_class`` is specified, the message is broadcasted to all
        actors.

        :param message: the message to send
        :type message: any

        :param target_class: optional actor class to broadcast the message to
        :type target_class: class or class name
        """
        if isinstance(target_class, str):
            targets = cls.get_by_class_name(target_class)
        elif target_class is not None:
            targets = cls.get_by_class(target_class)
        else:
            targets = cls.get_all()
        for ref in targets:
            ref.tell(message)

    @classmethod
    def get_all(cls) -> list[ActorRef[Any]]:
        """Get all running actors.

        :returns: list of :class:`pykka.asyncio.ActorRef`
        """
        return cls._actor_refs[:]

    @classmethod
    def get_by_class(
        cls,
        actor_class: type[A],
    ) -> list[ActorRef[A]]:
        """Get all running actors of the given class or a subclass.

        :param actor_class: actor class, or any superclass of the actor
        :type actor_class: class

        :returns: list of :class:`pykka.asyncio.ActorRef`
        """
        return [
            ref for ref in cls._actor_refs if issubclass(ref.actor_class, actor_class)
        ]

    @classmethod
    def get_by_class_name(
        cls,
        actor_class_name: str,
    ) -> list[ActorRef[Any]]:
        """Get all running actors of the given class name.

        :param actor_class_name: actor class name
        :type actor_class_name: string

        :returns: list of :class:`pykka.asyncio.ActorRef`
        """
        return [
            ref
            for ref in cls._actor_refs
            if ref.actor_class.__name__ == actor_class_name
        ]

    @classmethod
    def get_by_urn(
        cls,
        actor_urn: str,
    ) -> Optional[ActorRef[Any]]:
        """Get an actor by its universally unique URN.

        :param actor_urn: actor URN
        :type actor_urn: string

        :returns: :class:`pykka.asyncio.ActorRef` or :class:`None` if not found
        """
        refs = [ref for ref in cls._actor_refs if ref.actor_urn == actor_urn]
        if not refs:
            return None
        return refs[0]

    @classmethod
    def register(
        cls,
        actor_ref: ActorRef[Any],
    ) -> None:
        """Register an :class:`ActorRef` in the registry.

        This is done automatically when an actor is started, e.g. by calling
        :meth:`Actor.start() <pykka.Actor.start>`.

        :param actor_ref: reference to the actor to register
        :type actor_ref: :class:`pykka.asyncio.ActorRef`
        """
        cls._actor_refs.append(actor_ref)
        logger.debug(f"Registered {actor_ref}")

    @classmethod
    async def stop_all(
        cls,
        timeout: Optional[float] = None,
    ) -> list[bool]:
        """Stop all running actors.

        The actors are guaranteed to be stopped in the reverse of the
        order they were started in. This is helpful if you have simple
        dependencies in between your actors, where it is sufficient to
        shut down actors in a LIFO manner: last started, first
        stopped.

        If you have more complex dependencies in between your actors, you
        should take care to shut them down in the required order yourself, e.g.
        by stopping dependees from a dependency's
        :meth:`on_stop() <pykka.Actor.on_stop>` method.

        If order doesn't matter, consider awaiting
        :meth:`pykka.asyncio.ActorRef.stop` on ActorRefs using
        `asyncio.gather`.

        :returns: A list of return values from
            :meth:`pykka.asyncio.ActorRef.stop`.

        """
        return [
            await ref.stop().get(timeout=timeout) for ref in reversed(cls.get_all())
        ]

    @classmethod
    def unregister(
        cls,
        actor_ref: ActorRef[A],
    ) -> None:
        """Remove an :class:`ActorRef <pykka.ActorRef>` from the registry.

        This is done automatically when an actor is stopped, e.g. by calling
        :meth:`Actor.stop() <pykka.Actor.stop>`.

        :param actor_ref: reference to the actor to unregister
        :type actor_ref: :class:`pykka.ActorRef`
        """
        removed = False
        if actor_ref in cls._actor_refs:
            cls._actor_refs.remove(actor_ref)
            removed = True
        if removed:
            logger.debug(f"Unregistered {actor_ref}")
        else:
            logger.debug(f"Unregistered {actor_ref} (not found in registry)")
