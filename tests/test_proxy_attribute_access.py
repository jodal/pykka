import pytest


class NestedObject(object):
    pykka_traversable = True
    inner = 'nested.inner'


@pytest.fixture(scope='module')
def actor_class(runtime):
    class ActorA(runtime.actor_class):
        an_attr = 'an_attr'
        _private_attr = 'secret'
        nested = NestedObject()

    return ActorA


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_actor_attr_can_be_read_using_get_postfix(proxy):
    assert proxy.an_attr.get() == 'an_attr'


def test_actor_attr_can_be_set_using_assignment(proxy):
    assert proxy.an_attr.get() == 'an_attr'

    proxy.an_attr = 'an_attr_2'

    assert proxy.an_attr.get() == 'an_attr_2'


def test_private_attr_access_raises_exception(proxy):
    with pytest.raises(AttributeError):
        proxy._private_attr.get()


def test_attr_of_traversable_attr_can_be_read(proxy):
    assert proxy.nested.inner.get() == 'nested.inner'
