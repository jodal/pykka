import pytest


class NestedObject(object):
    pykka_traversable = True
    baz = 'bar.baz'


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        foo = 'foo'

        bar = NestedObject()

        _private_field = 'secret'

    return ActorA


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_actor_field_can_be_read_using_get_postfix(proxy):
    assert proxy.foo.get() == 'foo'


def test_actor_field_can_be_set_using_assignment(proxy):
    assert proxy.foo.get() == 'foo'

    proxy.foo = 'foo2'

    assert proxy.foo.get() == 'foo2'


def test_private_field_access_raises_exception(proxy):
    with pytest.raises(AttributeError):
        proxy._private_field.get()


def test_attr_of_traversable_attr_can_be_read(proxy):
    assert proxy.bar.baz.get() == 'bar.baz'
