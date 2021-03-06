import pytest

import pykka


class NestedWithNoMarker:
    inner = "nested_with_no_marker.inner"


class NestedWithNoMarkerAndSlots:
    __slots__ = ["inner"]

    def __init__(self):
        self.inner = "nested_with_no_marker_and_slots.inner"


@pykka.traversable
class NestedWithDecoratorMarker:
    inner = "nested_with_decorator_marker.inner"


class NestedWithAttrMarker:
    pykka_traversable = True
    inner = "nested_with_attr_marker.inner"


class NestedWithAttrMarkerAndSlots:
    __slots__ = ["pykka_traversable", "inner"]

    def __init__(self):
        # Objects using '__slots__' cannot have class attributes.
        self.pykka_traversable = True
        self.inner = "nested_with_attr_marker_and_slots.inner"


@pytest.fixture
def actor_class(runtime):
    class ActorWithTraversableObjects(runtime.actor_class):
        nested_with_no_marker = NestedWithNoMarker()
        nested_with_function_marker = pykka.traversable(NestedWithNoMarker())
        nested_with_decorator_marker = NestedWithDecoratorMarker()
        nested_with_attr_marker = NestedWithAttrMarker()
        nested_with_attr_marker_and_slots = NestedWithAttrMarkerAndSlots()

        @property
        def nested_object_property(self):
            return NestedWithAttrMarker()

    return ActorWithTraversableObjects


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_attr_without_marker_cannot_be_traversed(proxy):
    with pytest.raises(AttributeError) as exc_info:
        proxy.nested_with_no_marker.inner.get()

    assert "object has no attribute 'inner'" in str(exc_info.value)


@pytest.mark.parametrize(
    "attr_name, expected",
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
def test_attr_of_traversable_attr_can_be_read(proxy, attr_name, expected):
    attr = getattr(proxy, attr_name)

    assert attr.inner.get() == expected


def test_traversable_object_returned_from_property_is_not_traversed(proxy):
    # In Pykka < 2, it worked like this:
    # assert proxy.nested_object_property.inner.get() == 'nested.inner'

    # In Pykka >= 2, the property getter always returns a future:
    assert proxy.nested_object_property.get().inner == "nested_with_attr_marker.inner"


def test_traversable_cannot_mark_object_using_slots():
    with pytest.raises(Exception) as exc_info:
        pykka.traversable(NestedWithNoMarkerAndSlots())

    assert "cannot be used to mark an object using slots" in str(exc_info.value)
