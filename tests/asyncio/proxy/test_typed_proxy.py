from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncGenerator, cast

import pytest

from pykka.asyncio import Actor, ActorDeadError, ActorProxy, traversable
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

if TYPE_CHECKING:
    from tests.asyncio.types import Runtime


@dataclass
class Constants:
    pi: float


class CircleActor(Actor):
    constants = traversable(Constants(pi=3.14))
    text: str = "The fox crossed the road."

    def area(self, radius: float) -> float:
        return self.constants.pi * radius**2


class ConstantsProxy:
    pi = proxy_field(CircleActor.constants.pi)


class FooProxy(ActorMemberMixin, ActorProxy[CircleActor]):
    numbers: ConstantsProxy
    text = proxy_field(CircleActor.text)
    area = proxy_method(CircleActor.area)


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[CircleActor]:
    class FooActorImpl(CircleActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return FooActorImpl


@pytest.fixture()
async def proxy(
    actor_class: type[CircleActor],
) -> AsyncGenerator[FooProxy]:
    proxy = cast(FooProxy, actor_class.start().proxy())
    yield proxy
    try:
        await proxy.stop()
    except ActorDeadError:
        pass


async def test_proxy_field(proxy: FooProxy) -> None:
    assert await proxy.text == "The fox crossed the road."


async def test_proxy_traversable_object_field(proxy: FooProxy) -> None:
    assert await proxy.constants.pi == 3.14


async def test_proxy_method(proxy: FooProxy) -> None:
    assert await proxy.area(2.0) == 12.56


async def test_proxy_to_actor_methods(proxy: FooProxy) -> None:
    assert await proxy.stop() is None  # type: ignore[func-returns-value]
