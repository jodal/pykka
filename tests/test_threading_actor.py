from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pytest

from pykka import ThreadingActor

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykka import ActorRef


class RegularActor(ThreadingActor):
    pass


class DaemonActor(ThreadingActor):
    use_daemon_thread = True


@pytest.fixture()
def regular_actor_ref() -> Iterator[ActorRef[RegularActor]]:
    ref = RegularActor.start()
    yield ref
    ref.stop()


@pytest.fixture()
def daemon_actor_ref() -> Iterator[ActorRef[DaemonActor]]:
    ref = DaemonActor.start()
    yield ref
    ref.stop()


def test_actor_thread_is_named_after_pykka_actor_class(
    regular_actor_ref: ActorRef[RegularActor],
) -> None:
    alive_threads = threading.enumerate()
    alive_thread_names = [t.name for t in alive_threads]
    named_correctly = [
        name.startswith(RegularActor.__name__) for name in alive_thread_names
    ]

    assert any(named_correctly)


def test_actor_thread_is_not_daemonic_by_default(
    regular_actor_ref: ActorRef[RegularActor],
) -> None:
    alive_threads = threading.enumerate()
    actor_threads = [t for t in alive_threads if t.name.startswith("RegularActor")]

    assert len(actor_threads) == 1
    assert not actor_threads[0].daemon


def test_actor_thread_is_daemonic_if_use_daemon_thread_flag_is_set(
    daemon_actor_ref: ActorRef[DaemonActor],
) -> None:
    alive_threads = threading.enumerate()
    actor_threads = [t for t in alive_threads if t.name.startswith("DaemonActor")]

    assert len(actor_threads) == 1
    assert actor_threads[0].daemon
