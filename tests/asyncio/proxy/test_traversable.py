from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

import pytest

from pykka.asyncio import Actor, traversable

if TYPE_CHECKING:
    from pykka.asyncio import ActorProxy
    from tests.asyncio.types import Runtime


class NestedWithNoMarker:
    inner = "nested_with_no_marker.inner"


class NestedWithNoMarkerAndSlots:
    __slots__ = ["inner"]

    def __init__(self) -> None:
        self.inner = "nested_with_no_marker_and_slots.inner"


@traversable
class NestedWithDecoratorMarker:
    inner = "nested_with_decorator_marker.inner"


class NestedWithAttrMarker:
    pykka_traversable = True
    inner = "nested_with_attr_marker.inner"


class NestedWithAttrMarkerAndSlots:
    __slots__ = ["pykka_traversable", "inner"]

    def __init__(self) -> None:
        # Objects using '__slots__' cannot have class attributes.
        self.pykka_traversable = True
        self.inner = "nested_with_attr_marker_and_slots.inner"


class TraversableObjectsActor(Actor):
    nested_with_no_marker = NestedWithNoMarker()
    nested_with_function_marker = traversable(NestedWithNoMarker())
    nested_with_decorator_marker = NestedWithDecoratorMarker()
    nested_with_attr_marker = NestedWithAttrMarker()
    nested_with_attr_marker_and_slots = NestedWithAttrMarkerAndSlots()

    @property
    def nested_object_property(self) -> NestedWithAttrMarker:
        return NestedWithAttrMarker()


@pytest.fixture()
def actor_class(runtime: Runtime) -> type[Actor]:
    class TraversableObjectsActorImpl(TraversableObjectsActor, runtime.actor_class):  # type: ignore[name-defined]
        pass

    return TraversableObjectsActorImpl


@pytest.fixture()
async def proxy(
    actor_class: type[TraversableObjectsActor],
) -> AsyncGenerator[ActorProxy[TraversableObjectsActor]]:
    proxy = actor_class.start().proxy()
    yield proxy
    await proxy.stop()


async def test_attr_without_marker_cannot_be_traversed(
    proxy: ActorProxy[TraversableObjectsActor],
) -> None:
    with pytest.raises(AttributeError) as exc_info:
        await proxy.nested_with_no_marker.inner.get()

    assert "object has no attribute 'inner'" in str(exc_info.value)


@pytest.mark.parametrize(
    ("attr_name", "expected"),
    [
        ("nested_with_function_marker", "nested_with_no_marker.inner"),
        ("nested_with_decorator_marker", "nested_with_decorator_marker.inner"),
        ("nested_with_attr_marker", "nested_with_attr_marker.inner"),
        (
            "nested_with_attr_marker_and_slots",
            "nested_with_attr_marker_and_slots.inner",
        ),
    ],
)
async def test_attr_of_traversable_attr_can_be_read(
    proxy: ActorProxy[TraversableObjectsActor],
    attr_name: str,
    expected: str,
) -> None:
    attr = getattr(proxy, attr_name)

    assert await attr.inner.get() == expected


async def test_traversable_object_returned_from_property_is_not_traversed(
    proxy: ActorProxy[TraversableObjectsActor],
) -> None:
    # In Pykka < 2, it worked like this:
    # assert proxy.nested_object_property.inner.get() == 'nested.inner'  # noqa: ERA001

    # In Pykka >= 2, the property getter always returns a future:
    assert (
        await proxy.nested_object_property.get()
    ).inner == "nested_with_attr_marker.inner"


def test_traversable_cannot_mark_object_using_slots() -> None:
    with pytest.raises(Exception, match="cannot be used to mark") as exc_info:
        traversable(NestedWithNoMarkerAndSlots())

    assert "cannot be used to mark an object using slots" in str(exc_info.value)
