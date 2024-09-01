from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from pykka import Actor, ActorRegistry

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from pykka import ActorRef
    from tests.types import Runtime

pytestmark = pytest.mark.usefixtures("_stop_all")


class ActorBase(Actor):
    received_messages: list[Any]

    def __init__(self) -> None:
        super().__init__()
        self.received_messages = []

    def on_receive(self, message: Any) -> None:
        self.received_messages.append(message)


class ActorA(ActorBase):
    pass


class ActorB(ActorBase):
    pass


@pytest.fixture(scope="module")
def actor_a_class(runtime: Runtime) -> type[ActorA]:
    class ActorAImpl(ActorA, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ActorAImpl


@pytest.fixture(scope="module")
def actor_b_class(runtime: Runtime) -> type[ActorB]:
    class ActorBImpl(ActorB, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ActorBImpl


@pytest.fixture()
def actor_ref(actor_a_class: type[ActorA]) -> ActorRef[ActorA]:
    return actor_a_class.start()


@pytest.fixture()
def a_actor_refs(actor_a_class: type[ActorA]) -> list[ActorRef[ActorA]]:
    return [actor_a_class.start() for _ in range(3)]


@pytest.fixture()
def b_actor_refs(actor_b_class: type[ActorB]) -> list[ActorRef[ActorB]]:
    return [actor_b_class.start() for _ in range(5)]


def test_actor_is_registered_when_started(
    actor_ref: ActorRef[ActorA],
) -> None:
    assert actor_ref in ActorRegistry.get_all()


def test_actor_is_unregistered_when_stopped(
    actor_ref: ActorRef[ActorA],
) -> None:
    assert actor_ref in ActorRegistry.get_all()

    actor_ref.stop()

    assert actor_ref not in ActorRegistry.get_all()


def test_actor_may_be_registered_manually(
    actor_ref: ActorRef[ActorA],
) -> None:
    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.register(actor_ref)

    assert actor_ref in ActorRegistry.get_all()


def test_actor_may_be_unregistered_multiple_times_without_error(
    actor_ref: ActorRef[ActorA],
) -> None:
    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.unregister(actor_ref)
    assert actor_ref not in ActorRegistry.get_all()

    ActorRegistry.register(actor_ref)
    assert actor_ref in ActorRegistry.get_all()


def test_all_actors_can_be_stopped_through_registry(
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    assert len(ActorRegistry.get_all()) == 8

    ActorRegistry.stop_all(block=True)

    assert len(ActorRegistry.get_all()) == 0


def test_stop_all_stops_last_started_actor_first_if_blocking(
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(ActorRegistry, "get_all")

    stopped_actors = []
    started_actors = [mocker.Mock(name=f"{i}") for i in range(3)]
    started_actors[0].stop.side_effect = lambda *a, **kw: stopped_actors.append(  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
        started_actors[0]
    )
    started_actors[1].stop.side_effect = lambda *a, **kw: stopped_actors.append(  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
        started_actors[1]
    )
    started_actors[2].stop.side_effect = lambda *a, **kw: stopped_actors.append(  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
        started_actors[2]
    )
    ActorRegistry.get_all.return_value = (  # type: ignore[attr-defined]  # pyright: ignore[reportFunctionMemberAccess]
        started_actors
    )

    ActorRegistry.stop_all(block=True)

    assert stopped_actors[0] == started_actors[2]
    assert stopped_actors[1] == started_actors[1]
    assert stopped_actors[2] == started_actors[0]


def test_actors_may_be_looked_up_by_class(
    actor_a_class: type[ActorA],
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    result = ActorRegistry.get_by_class(actor_a_class)

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result  # type: ignore[comparison-overlap]


def test_actors_may_be_looked_up_by_superclass(
    actor_a_class: type[ActorA],
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    result = ActorRegistry.get_by_class(actor_a_class)

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result  # type: ignore[comparison-overlap]


def test_actors_may_be_looked_up_by_class_name(
    actor_a_class: type[ActorA],
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    result = ActorRegistry.get_by_class_name("ActorAImpl")

    for a_actor in a_actor_refs:
        assert a_actor in result
    for b_actor in b_actor_refs:
        assert b_actor not in result


def test_actors_may_be_looked_up_by_urn(
    actor_ref: ActorRef[ActorA],
) -> None:
    result = ActorRegistry.get_by_urn(actor_ref.actor_urn)

    assert result == actor_ref


def test_get_by_urn_returns_none_if_not_found() -> None:
    result = ActorRegistry.get_by_urn("urn:foo:bar")

    assert result is None


def test_broadcast_sends_message_to_all_actors_if_no_target(
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    ActorRegistry.broadcast({"command": "foo"})

    running_actors = ActorRegistry.get_all()
    assert running_actors

    for actor_ref in running_actors:
        received_messages = actor_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages


def test_broadcast_sends_message_to_all_actors_of_given_class(
    actor_a_class: type[ActorA],
    actor_b_class: type[ActorB],
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    ActorRegistry.broadcast({"command": "foo"}, target_class=actor_a_class)

    class_a_refs = ActorRegistry.get_by_class(actor_a_class)
    assert set(class_a_refs) == set(a_actor_refs)
    for actor_a_ref in class_a_refs:
        received_messages = actor_a_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages

    class_b_refs = ActorRegistry.get_by_class(actor_b_class)
    assert set(class_b_refs) == set(b_actor_refs)
    for actor_b_ref in class_b_refs:
        received_messages = actor_b_ref.proxy().received_messages.get()
        assert {"command": "foo"} not in received_messages


def test_broadcast_sends_message_to_all_actors_of_given_class_name(
    actor_a_class: type[ActorA],
    actor_b_class: type[ActorB],
    a_actor_refs: list[ActorRef[ActorA]],
    b_actor_refs: list[ActorRef[ActorB]],
) -> None:
    ActorRegistry.broadcast({"command": "foo"}, target_class="ActorAImpl")

    class_a_refs = ActorRegistry.get_by_class_name("ActorAImpl")
    assert set(class_a_refs) == set(a_actor_refs)
    for actor_a_ref in class_a_refs:
        received_messages = actor_a_ref.proxy().received_messages.get()
        assert {"command": "foo"} in received_messages

    class_b_refs = ActorRegistry.get_by_class_name("ActorBImpl")
    assert set(class_b_refs) == set(b_actor_refs)
    for actor_b_ref in class_b_refs:
        received_messages = actor_b_ref.proxy().received_messages.get()
        assert {"command": "foo"} not in received_messages
