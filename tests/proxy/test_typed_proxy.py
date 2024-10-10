from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

import pykka
from pykka import Actor, ActorProxy
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tests.types import Runtime


@dataclass
class Constants:
    pi: float


class CircleActor(Actor):
    constants = pykka.traversable(Constants(pi=3.14))
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
def proxy(
    actor_class: type[CircleActor],
) -> Iterator[FooProxy]:
    proxy = cast(FooProxy, actor_class.start().proxy())
    yield proxy
    proxy.stop()


def test_proxy_field(proxy: FooProxy) -> None:
    assert proxy.text.get() == "The fox crossed the road."


def test_proxy_traversable_object_field(proxy: FooProxy) -> None:
    assert proxy.constants.pi.get() == 3.14


def test_proxy_method(proxy: FooProxy) -> None:
    assert proxy.area(2.0).get() == 12.56


def test_proxy_to_actor_methods(proxy: FooProxy) -> None:
    assert proxy.stop().get() is None
