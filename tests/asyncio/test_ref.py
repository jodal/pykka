from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterator

import pytest

from pykka.asyncio import Actor, ActorDeadError, Timeout

if TYPE_CHECKING:
    from pykka.asyncio import ActorRef, Future
    from tests.types import Runtime


class ReferencableActor(Actor):
    received_messages = None

    def __init__(
        self,
        sleep_func: Callable[[float], Awaitable[None]],
        received_message: Future[str],
    ) -> None:
        super().__init__()
        self.sleep_func = sleep_func
        self.received_message = received_message

    async def on_receive(self, message: str) -> Any:
        if message == "ping":
            await self.sleep_func(0.01)
            return "pong"

        self.received_message.set(message)
        return None


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[ReferencableActor]:
    class ReferencableActorImpl(ReferencableActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return ReferencableActorImpl


@pytest.fixture()
async def received_message(runtime: Runtime) -> Future[str]:
    return runtime.future_class()


@pytest.fixture()
async def actor_ref(
    runtime: Runtime,
    actor_class: type[ReferencableActor],
    received_message: Future[str],
) -> Iterator[ActorRef[ReferencableActor]]:
    ref = await actor_class.start(
        runtime.sleep_func,
        received_message,
    )
    yield ref
    await ref.stop()


def test_repr_is_wrapped_in_lt_and_gt(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    result = repr(actor_ref)

    assert result.startswith("<")
    assert result.endswith(">")


def test_repr_reveals_that_this_is_a_ref(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert "ActorRef" in repr(actor_ref)


def test_repr_contains_actor_class_name(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert "ReferencableActor" in repr(actor_ref)


def test_repr_contains_actor_urn(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert actor_ref.actor_urn in repr(actor_ref)


def test_str_contains_actor_class_name(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert "ReferencableActor" in str(actor_ref)


def test_str_contains_actor_urn(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert actor_ref.actor_urn in str(actor_ref)


def test_is_alive_returns_true_for_running_actor(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert actor_ref.is_alive()


async def test_is_alive_returns_false_for_dead_actor(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    await actor_ref.stop()

    assert not actor_ref.is_alive()


async def test_stop_returns_true_if_actor_is_stopped(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert await actor_ref.stop()


async def test_stop_does_not_stop_already_dead_actor(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    assert await actor_ref.stop()
    assert not await actor_ref.stop()


async def test_tell_delivers_message_to_actors_custom_on_receive(
    actor_ref: ActorRef[ReferencableActor],
    received_message: Future[str],
) -> None:
    await actor_ref.tell("a custom message")

    assert await received_message.get(timeout=1) == "a custom message"


@pytest.mark.parametrize(
    "message",
    [
        123,
        123.456,
        {"a": "dict"},
        ("a", "tuple"),
        ["a", "list"],
        Exception("an exception"),
    ],
)
async def test_tell_accepts_any_object_as_the_message(
    actor_ref: ActorRef[ReferencableActor],
    message: Any,
    received_message: Future[Any],
) -> None:
    await actor_ref.tell(message)

    assert await received_message.get(timeout=1) == message


async def test_tell_fails_if_actor_is_stopped(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    await actor_ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        await actor_ref.tell("a custom message")

    assert str(exc_info.value) == f"{actor_ref} not found"


async def test_ask_blocks_until_response_arrives(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    result = await actor_ref.ask("ping")

    assert result == "pong"


# TODO
async def test_ask_can_timeout_if_blocked_too_long(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    with pytest.raises(Timeout):
        await actor_ref.ask("ping", timeout=0.01)


async def test_ask_can_return_future_instead_of_blocking(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    future = await actor_ref.ask("ping", block=False)

    assert await future.get() == "pong"


async def test_ask_fails_if_actor_is_stopped(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    await actor_ref.stop()

    with pytest.raises(ActorDeadError) as exc_info:
        await actor_ref.ask("ping")

    assert str(exc_info.value) == f"{actor_ref} not found"


async def test_ask_nonblocking_fails_future_if_actor_is_stopped(
    actor_ref: ActorRef[ReferencableActor],
) -> None:
    await actor_ref.stop()
    future = await actor_ref.ask("ping", block=False)

    with pytest.raises(ActorDeadError) as exc_info:
        await future.get()

    assert str(exc_info.value) == f"{actor_ref} not found"
