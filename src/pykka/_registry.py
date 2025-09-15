from __future__ import annotations

import logging
import threading
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    TypeVar,
    overload,
)

if TYPE_CHECKING:
    from pykka import Actor, ActorRef, Future

__all__ = ["ActorRegistry"]


logger = logging.getLogger("pykka")


A = TypeVar("A", bound="Actor")


class ActorRegistry:
    """Registry which provides easy access to all running actors.

    Contains global state, but should be thread-safe.
    """

    _actor_refs: ClassVar[list[ActorRef[Any]]] = []
    _actor_refs_lock: ClassVar[threading.RLock] = threading.RLock()

    @classmethod
    def broadcast(
        cls,
        message: Any,
        target_class: str | type[Actor] | None = None,
    ) -> None:
        """Broadcast `message` to all actors of the specified `target_class`.

        If no `target_class` is specified, the message is broadcasted to all
        actors.

        Args:
            message: the message to send
            target_class: optional actor class or class name

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
        """Get all running actors."""
        with cls._actor_refs_lock:
            return cls._actor_refs[:]

    @classmethod
    def get_by_class(
        cls,
        actor_class: type[A],
    ) -> list[ActorRef[A]]:
        """Get all running actors of the given class or a subclass.

        Args:
            actor_class: actor class, or any superclass of the actor

        """
        with cls._actor_refs_lock:
            return [
                ref
                for ref in cls._actor_refs
                if issubclass(ref.actor_class, actor_class)
            ]

    @classmethod
    def get_by_class_name(
        cls,
        actor_class_name: str,
    ) -> list[ActorRef[Any]]:
        """Get all running actors of the given class name."""
        with cls._actor_refs_lock:
            return [
                ref
                for ref in cls._actor_refs
                if ref.actor_class.__name__ == actor_class_name
            ]

    @classmethod
    def get_by_urn(
        cls,
        actor_urn: str,
    ) -> ActorRef[Any] | None:
        """Get an actor by its universally unique URN."""
        with cls._actor_refs_lock:
            refs = [ref for ref in cls._actor_refs if ref.actor_urn == actor_urn]
            if not refs:
                return None
            return refs[0]

    @classmethod
    def register(
        cls,
        actor_ref: ActorRef[Any],
    ) -> None:
        """Register an [`ActorRef`][pykka.ActorRef] in the registry.

        This is done automatically when an actor is started, e.g. by calling
        [`Actor.start()`][pykka.Actor.start].
        """
        with cls._actor_refs_lock:
            cls._actor_refs.append(actor_ref)
        logger.debug(f"Registered {actor_ref}")

    @overload
    @classmethod
    def stop_all(
        cls,
        *,
        block: Literal[True],
        timeout: float | None = ...,
    ) -> list[bool]: ...

    @overload
    @classmethod
    def stop_all(
        cls,
        *,
        block: Literal[False],
        timeout: float | None = ...,
    ) -> list[Future[bool]]: ...

    @overload
    @classmethod
    def stop_all(
        cls,
        *,
        block: bool = True,
        timeout: float | None = None,
    ) -> list[bool] | list[Future[bool]]: ...

    @classmethod
    def stop_all(
        cls,
        *,
        block: bool = True,
        timeout: float | None = None,
    ) -> list[bool] | list[Future[bool]]:
        """Stop all running actors.

        `block` and `timeout` works as for
        [`ActorRef.stop()`][pykka.ActorRef.stop].

        If `block` is `True`, the actors are guaranteed to be stopped
        in the reverse of the order they were started in. This is helpful if
        you have simple dependencies in between your actors, where it is
        sufficient to shut down actors in a LIFO manner: last started, first
        stopped.

        If you have more complex dependencies in between your actors, you
        should take care to shut them down in the required order yourself, e.g.
        by stopping dependees from a dependency's
        [`on_stop()`][pykka.Actor.on_stop] method.

        Returns:
            a list with the return values for each stop action

        """
        return [  # type: ignore[return-value]
            ref.stop(block=block, timeout=timeout) for ref in reversed(cls.get_all())
        ]

    @classmethod
    def unregister(
        cls,
        actor_ref: ActorRef[A],
    ) -> None:
        """Remove an [`ActorRef`][pykka.ActorRef] from the registry.

        This is done automatically when an actor is stopped, e.g. by calling
        [`Actor.stop()`][pykka.Actor.stop].
        """
        removed = False
        with cls._actor_refs_lock:
            if actor_ref in cls._actor_refs:
                cls._actor_refs.remove(actor_ref)
                removed = True
        if removed:
            logger.debug(f"Unregistered {actor_ref}")
        else:
            logger.debug(f"Unregistered {actor_ref} (not found in registry)")
