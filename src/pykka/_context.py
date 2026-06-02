from __future__ import annotations

import contextlib
import contextvars
import threading
import weakref
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykka import Actor

__all__: list[str] = []


class ActorContext:
    """A node in the actor hierarchy tree.

    Each started actor has an associated context which records its parent
    context (the context of the actor that started it, or the module-level
    [`ROOT`][pykka._context.ROOT] for top-level actors) and the contexts of
    actors started by it.

    The tree is currently used only to track parent/child relationships and is
    not exposed in the public API. It is intended to become the basis for
    supervision and debug introspection.
    """

    parent: ActorContext | None
    """The parent context, or [`None`][None] for the root context."""

    def __init__(
        self,
        actor: Actor | None,
        parent: ActorContext | None,
    ) -> None:
        self._actor_weakref: weakref.ref[Actor] | None = (
            weakref.ref(actor) if actor is not None else None
        )
        self.parent = parent
        self._children: list[ActorContext] = []
        self._lock = threading.RLock()

    @property
    def actor(self) -> Actor | None:
        """The actor associated with this context, or [`None`][None] for [`ROOT`][pykka._context.ROOT] and dead actors."""  # noqa: E501
        return self._actor_weakref() if self._actor_weakref is not None else None

    def add_child(self, child: ActorContext) -> None:
        """Append `child` to the list of children.

        Children are stored in start order; the most recently started child is
        last in the list.
        """
        with self._lock:
            self._children.append(child)

    def remove_child(self, child: ActorContext) -> None:
        """Remove `child` from the list of children.

        Idempotent: removing a child that is not present is a no-op.
        """
        with self._lock, contextlib.suppress(ValueError):
            self._children.remove(child)

    def children(self) -> list[ActorContext]:
        """Return a snapshot of the current children, in start order."""
        with self._lock:
            return list(self._children)


ROOT: ActorContext = ActorContext(actor=None, parent=None)
"""The shared root of the actor context tree.

Actors started outside any actor become children of [`ROOT`][pykka._context.ROOT].
"""


_current_context: contextvars.ContextVar[ActorContext] = contextvars.ContextVar(
    "pykka_current_actor_context"
)
"""[`ContextVar`][contextvars.ContextVar] holding the running actor's context.

Set inside the actor's own loop (in
[`Actor._actor_loop_setup`][pykka.Actor._actor_loop_setup]) so that
[`Actor.start`][pykka.Actor.start] called from within an actor can find the
parent context. Unset elsewhere; callers should use `.get(ROOT)`.
"""
