from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import pytest

from pykka import Actor, ActorDeadError, ActorRegistry

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykka import ActorRef
    from tests.types import Events, Runtime

pytestmark = pytest.mark.usefixtures("_stop_all")


class AnActor(Actor):
    def __init__(self, events: Events) -> None:
        super().__init__()
        self.events = events

    def on_start(self) -> None:
        self.events.on_start_was_called.set()
        if ActorRegistry.get_by_urn(self.actor_urn) is not None:
            self.events.actor_registered_before_on_start_was_called.set()

    def on_stop(self) -> None:
        self.events.on_stop_was_called.set()

    def on_failure(self, *args: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        self.events.on_failure_was_called.set()

    def on_receive(self, message: Any) -> None:
        if message.get("command") == "raise exception":
            raise Exception("foo")

        if message.get("command") == "raise base exception":
            raise BaseException

        if message.get("command") == "stop twice":
            self.stop()
            self.stop()
        elif message.get("command") == "message self then stop":
            self.actor_ref.tell({"command": "greetings"})
            self.stop()
        elif message.get("command") == "greetings":
            self.events.greetings_was_received.set()
        elif message.get("command") == "callback":
            message["callback"]()
        else:
            super().on_receive(message)


class EarlyStoppingActor(Actor):
    def __init__(self, events: Events) -> None:
        super().__init__()
        self.events = events

    def on_start(self) -> None:
        self.stop()

    def on_stop(self) -> None:
        self.events.on_stop_was_called.set()


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[AnActor]:
    class ActorAImpl(AnActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ActorAImpl


@pytest.fixture()
def actor_ref(
    actor_class: type[AnActor],
    events: Events,
) -> Iterator[ActorRef[AnActor]]:
    ref = actor_class.start(events)
    yield ref
    ref.stop()


@pytest.fixture(scope="module")
def early_stopping_actor_class(runtime: Runtime) -> type[EarlyStoppingActor]:
    class EarlyStoppingActorImpl(EarlyStoppingActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return EarlyStoppingActorImpl


def test_messages_left_in_queue_after_actor_stops_receive_an_error(
    runtime: Runtime,
    actor_ref: ActorRef[AnActor],
) -> None:
    event = runtime.event_class()

    actor_ref.tell({"command": "callback", "callback": event.wait})
    actor_ref.stop(block=False)
    response = actor_ref.ask({"command": "irrelevant"}, block=False)
    event.set()

    with pytest.raises(ActorDeadError):
        response.get(timeout=0.5)


def test_stop_requests_left_in_queue_after_actor_stops_are_handled(
    runtime: Runtime,
    actor_ref: ActorRef[AnActor],
) -> None:
    event = runtime.event_class()

    actor_ref.tell({"command": "callback", "callback": event.wait})
    actor_ref.stop(block=False)
    response = actor_ref.stop(block=False)
    event.set()

    response.get(timeout=0.5)


def test_actor_has_an_uuid4_based_urn(actor_ref: ActorRef[AnActor]) -> None:
    assert uuid.UUID(actor_ref.actor_urn).version == 4


def test_actor_has_unique_uuid(
    actor_class: type[AnActor],
    events: Events,
) -> None:
    actors = [actor_class.start(events) for _ in range(3)]

    assert actors[0].actor_urn != actors[1].actor_urn
    assert actors[1].actor_urn != actors[2].actor_urn
    assert actors[2].actor_urn != actors[0].actor_urn


def test_str_on_raw_actor_contains_actor_class_name(
    actor_class: type[AnActor],
    events: Events,
) -> None:
    unstarted_actor = actor_class(events)

    assert "ActorA" in str(unstarted_actor)


def test_str_on_raw_actor_contains_actor_urn(
    actor_class: type[AnActor],
    events: Events,
) -> None:
    unstarted_actor = actor_class(events)

    assert unstarted_actor.actor_urn in str(unstarted_actor)


def test_init_can_be_called_with_arbitrary_arguments(runtime: Runtime) -> None:
    runtime.actor_class(1, 2, 3, foo="bar")


def test_on_start_is_called_before_first_message_is_processed(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    events.on_start_was_called.wait(5)
    assert events.on_start_was_called.is_set()


def test_on_start_is_called_after_the_actor_is_registered(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    # NOTE: If the actor is registered after the actor is started, this
    # test may still occasionally pass, as it is dependant on the exact
    # timing of events. When the actor is first registered and then
    # started, this test should always pass.
    events.on_start_was_called.wait(5)
    assert events.on_start_was_called.is_set()

    events.actor_registered_before_on_start_was_called.wait(0.1)
    assert events.actor_registered_before_on_start_was_called.is_set()


def test_on_start_can_stop_actor_before_receive_loop_is_started(
    early_stopping_actor_class: type[AnActor],
    events: Events,
) -> None:
    # NOTE: This test will pass even if the actor is allowed to start the
    # receive loop, but it will cause the test suite to hang, as the actor
    # thread is blocking on receiving messages to the actor inbox forever.
    # If one made this test specifically for ThreadingActor, one could add
    # an assertFalse(actor_thread.is_alive()), which would cause the test
    # to fail properly.
    actor_ref = early_stopping_actor_class.start(events)

    events.on_stop_was_called.wait(5)
    assert events.on_stop_was_called.is_set()
    assert not actor_ref.is_alive()


def test_on_start_failure_causes_actor_to_stop(
    early_failing_actor_class: type[AnActor],
    events: Events,
) -> None:
    # Actor should not be alive if on_start fails.

    actor_ref = early_failing_actor_class.start(events)
    events.on_start_was_called.wait(5)

    actor_ref.actor_stopped.wait(5)
    assert not actor_ref.is_alive()


def test_on_stop_is_called_when_actor_is_stopped(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    assert not events.on_stop_was_called.is_set()

    actor_ref.stop()

    events.on_stop_was_called.wait(5)
    assert events.on_stop_was_called.is_set()


def test_on_stop_failure_causes_actor_to_stop(
    late_failing_actor_class: type[AnActor],
    events: Events,
) -> None:
    actor_ref = late_failing_actor_class.start(events)

    events.on_stop_was_called.wait(5)
    assert not actor_ref.is_alive()


def test_on_failure_is_called_when_exception_cannot_be_returned(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    assert not events.on_failure_was_called.is_set()

    actor_ref.tell({"command": "raise exception"})

    events.on_failure_was_called.wait(5)
    assert events.on_failure_was_called.is_set()
    assert not events.on_stop_was_called.is_set()


def test_on_failure_failure_causes_actor_to_stop(
    failing_on_failure_actor_class: type[AnActor],
    events: Events,
) -> None:
    actor_ref = failing_on_failure_actor_class.start(events)

    actor_ref.tell({"command": "raise exception"})

    events.on_failure_was_called.wait(5)
    assert not actor_ref.is_alive()


def test_actor_is_stopped_when_unhandled_exceptions_are_raised(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    assert not events.on_failure_was_called.is_set()

    actor_ref.tell({"command": "raise exception"})

    events.on_failure_was_called.wait(5)
    assert events.on_failure_was_called.is_set()
    assert len(ActorRegistry.get_all()) == 0


def test_all_actors_are_stopped_on_base_exception(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    assert len(ActorRegistry.get_all()) == 1
    assert not events.on_stop_was_called.is_set()

    actor_ref.tell({"command": "raise base exception"})

    events.on_stop_was_called.wait(5)
    assert events.on_stop_was_called.is_set()
    assert len(ActorRegistry.get_all()) == 0

    events.on_stop_was_called.wait(5)
    assert events.on_stop_was_called.is_set()
    assert len(ActorRegistry.get_all()) == 0


def test_actor_can_call_stop_on_self_multiple_times(
    actor_ref: ActorRef[AnActor],
) -> None:
    actor_ref.ask({"command": "stop twice"})


def test_actor_processes_all_messages_before_stop_on_self_stops_it(
    actor_ref: ActorRef[AnActor],
    events: Events,
) -> None:
    actor_ref.ask({"command": "message self then stop"})

    events.greetings_was_received.wait(5)
    assert events.greetings_was_received.is_set()

    events.on_stop_was_called.wait(5)
    assert len(ActorRegistry.get_all()) == 0
