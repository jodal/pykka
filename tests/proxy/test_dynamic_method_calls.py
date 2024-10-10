from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pykka import Actor

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykka import ActorProxy, Future
    from tests.types import Runtime


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
def proxy(
    actor_class: type[DynamicMethodActor],
) -> Iterator[ActorProxy[DynamicMethodActor]]:
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_can_call_method_that_was_added_at_runtime(
    proxy: ActorProxy[DynamicMethodActor],
) -> None:
    # We need to .get() after .add_method() to be sure that the method has
    # been added before we try to use it through the proxy.
    proxy.add_method("foo").get()

    assert proxy.foo().get() == "returned by foo"


def test_can_proxy_itself_and_use_attrs_added_at_runtime(
    proxy: ActorProxy[DynamicMethodActor],
) -> None:
    # We don't need to .get() after .add_method() here, because the actor
    # will process the .add_method() call before processing the
    # .use_foo_through_self_proxy() call, which again will use the new
    # method, .foo().
    proxy.add_method("foo")

    outer_future = proxy.use_foo_through_self_proxy()
    inner_future = outer_future.get(timeout=1)
    result = inner_future.get(timeout=1)

    assert result == "returned by foo"
