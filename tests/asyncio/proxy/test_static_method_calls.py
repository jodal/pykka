from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, AsyncGenerator, Callable, NoReturn

import pytest

from pykka.asyncio import Actor, ActorDeadError

if TYPE_CHECKING:
    from pykka.asyncio import ActorProxy, Future
    from tests.asyncio.types import Events, Runtime


class StaticMethodActor(Actor):
    cat: str = "dog"

    def __init__(self, events: Events) -> None:
        super().__init__()
        self.events = events

    async def on_stop(self) -> None:
        self.events.on_stop_was_called.set()

    async def on_failure(self, *_args: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        self.events.on_failure_was_called.set()

    def functional_hello(self, s: str) -> str:
        return f"Hello, {s}!"

    async def async_hello(self, s: str) -> str:
        return f"Hello, {s}!"

    def set_cat(self, s: str) -> None:
        self.cat = s

    def raise_exception(self) -> NoReturn:
        raise Exception("boom!")

    def talk_with_self(self) -> Future[str]:
        return self.actor_ref.proxy().functional_hello("from the future")  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[StaticMethodActor]:
    class StaticMethodActorImpl(StaticMethodActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return StaticMethodActorImpl


@pytest.fixture()
async def proxy(
    actor_class: type[StaticMethodActor],
    events: Events,
) -> AsyncGenerator[ActorProxy[StaticMethodActor]]:
    proxy = actor_class.start(events).proxy()
    yield proxy
    try:
        await proxy.stop()
    except ActorDeadError:
        pass


async def test_functional_method_call_returns_correct_value(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    assert await proxy.functional_hello("world") == "Hello, world!"
    assert await proxy.functional_hello("moon") == "Hello, moon!"


async def test_async_method_call_returns_correct_value(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    assert await proxy.async_hello("world") == "Hello, world!"
    assert await proxy.async_hello("moon") == "Hello, moon!"



async def test_side_effect_of_method_call_is_observable(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    assert await proxy.cat == "dog"

    future = proxy.set_cat("eagle")

    assert await future is None
    assert await proxy.cat == "eagle"


async def test_side_effect_of_deferred_method_call_is_observable(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    assert await proxy.cat == "dog"

    result = proxy.set_cat.defer("eagle")

    assert result is None
    assert await proxy.cat == "eagle"


async def test_exception_in_method_reraised_by_future(
    proxy: ActorProxy[StaticMethodActor],
    events: Events,
) -> None:
    assert not events.on_failure_was_called.is_set()

    future = proxy.raise_exception()
    with pytest.raises(Exception, match="boom!") as exc_info:
        await future

    assert str(exc_info.value) == "boom!"
    assert not events.on_failure_was_called.is_set()


async def test_exception_in_deferred_method_call_triggers_on_failure(
    proxy: ActorProxy[StaticMethodActor],
    events: Events,
) -> None:
    assert not events.on_failure_was_called.is_set()

    result = proxy.raise_exception.defer()

    assert result is None
    await events.on_failure_was_called.wait(5)
    assert events.on_failure_was_called.is_set()
    assert not events.on_stop_was_called.is_set()


async def test_call_to_unknown_method_raises_attribute_error(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    with pytest.raises(AttributeError) as exc_info:
        await proxy.unknown_method()

    result = str(exc_info.value)

    assert result.startswith("<ActorProxy for StaticMethodActor")
    assert result.endswith("has no attribute 'unknown_method'")


def test_deferred_call_to_unknown_method_raises_attribute_error(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    with pytest.raises(AttributeError) as exc_info:
        proxy.unknown_method.defer()

    result = str(exc_info.value)

    assert result.startswith("<ActorProxy for StaticMethodActor")
    assert result.endswith("has no attribute 'unknown_method'")


async def test_can_proxy_itself_for_offloading_work_to_the_future(
    proxy: ActorProxy[StaticMethodActor],
) -> None:
    outer_future = proxy.talk_with_self()
    inner_future = await outer_future.get(timeout=1)

    result = await inner_future.get(timeout=1)

    assert result == "Hello, from the future!"
