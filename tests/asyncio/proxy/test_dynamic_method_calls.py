from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

import pytest

from pykka.asyncio import Actor

if TYPE_CHECKING:
    from pykka.asyncio import ActorProxy, Future
    from tests.asyncio.types import Runtime


class DynamicMethodActor(Actor):
    def add_method(self, name: str) -> None:
        setattr(self, name, lambda: "returned by " + name)

    def use_foo_through_self_proxy(self) -> Future[str]:
        return self.actor_ref.proxy().foo()  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def actor_class(runtime: Runtime) -> type[DynamicMethodActor]:
    class DynamicMethodActorImpl(DynamicMethodActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return DynamicMethodActorImpl


@pytest.fixture()
async def proxy(
    actor_class: type[DynamicMethodActor],
) -> AsyncGenerator[ActorProxy[DynamicMethodActor]]:
    proxy = actor_class.start().proxy()
    yield proxy
    await proxy.stop()


async def test_can_call_method_that_was_added_at_runtime(
    proxy: ActorProxy[DynamicMethodActor],
) -> None:
    await proxy.add_method("foo")

    assert await proxy.foo() == "returned by foo"


async def test_can_proxy_itself_and_use_attrs_added_at_runtime(
    proxy: ActorProxy[DynamicMethodActor],
) -> None:
    # We don't need to .get() after .add_method() here, because the actor
    # will process the .add_method() call before processing the
    # .use_foo_through_self_proxy() call, which again will use the new
    # method, .foo().
    await proxy.add_method("foo")

    outer_future = proxy.use_foo_through_self_proxy()
    inner_future = await outer_future.get(timeout=1)
    result = await inner_future.get(timeout=1)

    assert result == "returned by foo"
