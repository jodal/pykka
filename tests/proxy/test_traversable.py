import pytest


class NestedObject(object):
    pykka_traversable = True
    inner = 'nested.inner'


class NestedObjectWithSlots(object):
    __slots__ = ['pykka_traversable', 'inner']

    def __init__(self):
        # Objects using '__slots__' cannot have class attributes.
        self.pykka_traversable = True
        self.inner = 'nested_with_slots.inner'


@pytest.fixture
def actor_class(runtime):
    class ActorWithTraversableObjects(runtime.actor_class):
        nested = NestedObject()
        nested_with_slots = NestedObjectWithSlots()

        @property
        def nested_object_property(self):
            return NestedObject()

    return ActorWithTraversableObjects


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_attr_of_traversable_attr_can_be_read(proxy):
    assert proxy.nested.inner.get() == 'nested.inner'


def test_traversable_object_returned_from_property_is_not_traversed(proxy):
    # In Pykka < 2, it worked like this:
    # assert proxy.nested_object_property.inner.get() == 'nested.inner'

    # In Pykka >= 2, the property getter always returns a future:
    assert proxy.nested_object_property.get().inner == 'nested.inner'


def test_traversable_object_using_slots_works(proxy):
    assert proxy.nested_with_slots.inner.get() == 'nested_with_slots.inner'
