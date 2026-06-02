from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import pytest

import pykka
from pykka import Actor, ActorRegistry
from pykka._context import ROOT, ActorContext, _current_context

if TYPE_CHECKING:
    from tests.types import Runtime


pytestmark = pytest.mark.usefixtures("_stop_all")


class ContextProbe(Actor):
    """Actor that captures its own context.

    If `spawn_count > 0`, spawns that many bare `ContextProbe` children
    (each with `spawn_count=0`) during `on_start`, so the spawning chain
    terminates at depth 1.
    """

    def __init__(self, spawn_count: int = 0) -> None:
        super().__init__()
        self.context: ActorContext | None = None
        self._spawn_count = spawn_count
        self.child_refs: list[pykka.ActorRef[Any]] = []
        self.child_contexts: list[ActorContext] = []
        self.on_start_done = threading.Event()

    def on_start(self) -> None:
        self.context = self._actor_context
        for _ in range(self._spawn_count):
            self._spawn_child()
        self.on_start_done.set()

    def spawn_child(self) -> pykka.ActorRef[Any]:
        return self._spawn_child()

    def _spawn_child(self) -> pykka.ActorRef[Any]:
        cls = type(self)
        ref = cls.start(spawn_count=0)
        self.child_refs.append(ref)
        child_actor = ref._actor_weakref()  # noqa: SLF001
        assert child_actor is not None
        assert child_actor.on_start_done.wait(timeout=5)
        assert child_actor.context is not None
        self.child_contexts.append(child_actor.context)
        return ref


class FailingInOnStartProbe(Actor):
    def __init__(self) -> None:
        super().__init__()
        self.context: ActorContext | None = None

    def on_start(self) -> None:
        self.context = self._actor_context
        raise RuntimeError("on_start failure")


class FailingInOnReceiveProbe(Actor):
    def __init__(self) -> None:
        super().__init__()
        self.context: ActorContext | None = None

    def on_start(self) -> None:
        self.context = self._actor_context

    def on_receive(self, message: Any) -> Any:
        del message
        raise RuntimeError("on_receive failure")


@pytest.fixture(scope="module")
def probe_class(runtime: Runtime) -> type[ContextProbe]:
    class ContextProbeImpl(ContextProbe, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ContextProbeImpl


@pytest.fixture(scope="module")
def failing_on_start_probe_class(runtime: Runtime) -> type[FailingInOnStartProbe]:
    class FailingInOnStartProbeImpl(FailingInOnStartProbe, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return FailingInOnStartProbeImpl


@pytest.fixture(scope="module")
def failing_on_receive_probe_class(
    runtime: Runtime,
) -> type[FailingInOnReceiveProbe]:
    actor_class = runtime.actor_class

    class FailingInOnReceiveProbeImpl(FailingInOnReceiveProbe, actor_class):  # type: ignore[misc, valid-type]
        pass

    return FailingInOnReceiveProbeImpl


def _get_actor(ref: pykka.ActorRef[Any]) -> Any:
    actor = ref._actor_weakref()  # noqa: SLF001
    assert actor is not None
    return actor


def _wait_until_not_in(
    ctx: ActorContext,
    parent: ActorContext,
    timeout: float = 5.0,
) -> bool:
    waiter = threading.Event()
    step = 0.01
    waited = 0.0
    while waited < timeout:
        if ctx not in parent.children():
            return True
        waiter.wait(step)
        waited += step
    return False


def test_top_level_actor_is_child_of_root(
    probe_class: type[ContextProbe],
) -> None:
    ref = probe_class.start()
    actor = _get_actor(ref)
    assert actor.on_start_done.wait(5)

    assert actor.context is not None
    assert actor.context.parent is ROOT
    assert actor.context in ROOT.children()
    assert actor.context.actor is actor


def test_child_spawned_in_on_start_has_correct_parent(
    probe_class: type[ContextProbe],
) -> None:
    parent_ref = probe_class.start(spawn_count=1)
    parent_actor = _get_actor(parent_ref)
    assert parent_actor.on_start_done.wait(5)

    assert parent_actor.context is not None
    assert len(parent_actor.child_contexts) == 1
    child_context = parent_actor.child_contexts[0]
    assert child_context.parent is parent_actor.context
    assert child_context in parent_actor.context.children()


def test_children_appended_in_start_order(
    probe_class: type[ContextProbe],
) -> None:
    parent_ref = probe_class.start(spawn_count=3)
    parent_actor = _get_actor(parent_ref)
    assert parent_actor.on_start_done.wait(5)

    children = parent_actor.context.children()
    assert children == parent_actor.child_contexts
    assert len(children) == 3


def test_grandchildren_deep_nesting(
    probe_class: type[ContextProbe],
) -> None:
    grandparent_ref = probe_class.start()
    grandparent_actor = _get_actor(grandparent_ref)
    assert grandparent_actor.on_start_done.wait(5)

    parent_ref = grandparent_ref.proxy().spawn_child().get(timeout=5)
    parent_actor = _get_actor(parent_ref)
    child_ref = parent_ref.proxy().spawn_child().get(timeout=5)
    child_actor = _get_actor(child_ref)

    assert child_actor.context.parent is parent_actor.context
    assert parent_actor.context.parent is grandparent_actor.context
    assert grandparent_actor.context.parent is ROOT


def test_child_removed_from_parent_on_clean_stop(
    probe_class: type[ContextProbe],
) -> None:
    parent_ref = probe_class.start()
    parent_actor = _get_actor(parent_ref)
    assert parent_actor.on_start_done.wait(5)

    child_ref = parent_ref.proxy().spawn_child().get(timeout=5)
    child_context = parent_actor.child_contexts[0]
    assert child_context in parent_actor.context.children()

    child_ref.stop(block=True, timeout=5)

    assert _wait_until_not_in(child_context, parent_actor.context)


def test_child_removed_on_unhandled_exception_in_on_receive(
    failing_on_receive_probe_class: type[FailingInOnReceiveProbe],
) -> None:
    ref = failing_on_receive_probe_class.start()
    actor = _get_actor(ref)
    # Wait until on_start has captured the context.
    for _ in range(500):
        if actor.context is not None:
            break
        threading.Event().wait(0.005)
    assert actor.context in ROOT.children()

    ref.tell({"command": "boom"})
    ref.actor_stopped.wait(5)

    assert _wait_until_not_in(actor.context, ROOT)


def test_child_removed_when_on_start_raises(
    failing_on_start_probe_class: type[FailingInOnStartProbe],
) -> None:
    ref = failing_on_start_probe_class.start()
    actor = _get_actor(ref)
    ref.actor_stopped.wait(5)

    assert actor.context is not None
    assert _wait_until_not_in(actor.context, ROOT)


def test_context_var_reset_after_actor_stops(
    probe_class: type[ContextProbe],
) -> None:
    ref = probe_class.start()
    ref.stop(block=True, timeout=5)

    # Starting another actor afterwards must still find ROOT as parent,
    # not a stale context.
    new_ref = probe_class.start()
    new_actor = _get_actor(new_ref)
    assert new_actor.on_start_done.wait(5)
    assert new_actor.context.parent is ROOT


def test_actor_started_from_outside_any_actor_has_root_parent(
    probe_class: type[ContextProbe],
) -> None:
    ref = probe_class.start()
    actor = _get_actor(ref)
    assert actor.on_start_done.wait(5)

    assert actor.context.parent is ROOT


def test_concurrent_spawns_under_same_parent(
    probe_class: type[ContextProbe],
) -> None:
    parent_ref = probe_class.start()
    parent_actor = _get_actor(parent_ref)
    assert parent_actor.on_start_done.wait(5)

    futures = [parent_ref.proxy().spawn_child() for _ in range(10)]
    for f in futures:
        f.get(timeout=5)

    children = parent_actor.context.children()
    assert len(children) == 10
    assert all(c.parent is parent_actor.context for c in children)


def test_actor_context_not_in_public_api() -> None:
    assert "ActorContext" not in pykka.__all__
    assert not hasattr(pykka, "ActorContext")


def test_actor_context_not_exposed_via_actor_ref(
    probe_class: type[ContextProbe],
) -> None:
    ref = probe_class.start()

    assert not hasattr(ref, "actor_context")
    assert not hasattr(ref, "_actor_context")


def test_root_remains_after_all_actors_stop(
    probe_class: type[ContextProbe],
) -> None:
    ref1 = probe_class.start()
    ref2 = probe_class.start()
    ref1.stop(block=True, timeout=5)
    ref2.stop(block=True, timeout=5)

    assert ROOT.parent is None
    assert ROOT.actor is None


def test_context_var_has_no_default_outside_actor() -> None:
    sentinel: Any = object()
    assert _current_context.get(sentinel) is sentinel


def test_stop_all_clears_started_actors_from_root(
    probe_class: type[ContextProbe],
) -> None:
    ref_a = probe_class.start()
    ref_b = probe_class.start()
    actor_a = _get_actor(ref_a)
    actor_b = _get_actor(ref_b)
    assert actor_a.on_start_done.wait(5)
    assert actor_b.on_start_done.wait(5)
    ctx_a = actor_a.context
    ctx_b = actor_b.context
    assert ctx_a in ROOT.children()
    assert ctx_b in ROOT.children()

    ActorRegistry.stop_all(block=True, timeout=5)

    assert _wait_until_not_in(ctx_a, ROOT)
    assert _wait_until_not_in(ctx_b, ROOT)
